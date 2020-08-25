import sys
from typing import Union, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAction, QMenu


class TreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        """Disables sorting"""
        return False


# Constants to access data from TreeWidgetItems using the .data(0, DATA_SLOT) method
DISPLAY_NAME_SLOT = 0  # Display name
DATA_SLOT = 32  # Name of widget item
LEVEL_SLOT = 33  # 0 for top level, 1 for child of top levels
CHECKLIST_SLOT = 34  # Items to check
INDEX_SLOT = 35  # Index of child items under parent
DEPENDENT_SLOT = 37  # Items this current item depends on


class ParameterTree(QTreeWidget):
    """Holds parameters and their respective options"""

    max_size = 400
    move_request = pyqtSignal(QTreeWidgetItem, bool)
    addOption = pyqtSignal(QTreeWidgetItem)
    itemRemoved = pyqtSignal(QTreeWidgetItem, int)

    def __init__(self, profile: dict, parent=None):
        """
        Data table:
        All data is in column 0.
        --
        TODO: Make the following a enum or something class attributes.
        0  - Visual name.
        32 - main data entry, name of parents, full data for children
        33 - 0 for parent, 1 for children, 3 for custom option.
        34 - Name of item that needs to be checked
        35 - index for children used for active option
        37 - List of QModelIndex to items that this depends on.

        """
        super().__init__(parent=parent)

        self.favorite = False

        self.setExpandsOnDoubleClick(False)
        # self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setHeaderHidden(True)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        # self.header().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        # self.headerItem().setResizeMode(QHeaderView.ResizeToContents)

        # self.setItemWidget()
        if isinstance(profile, dict):
            self.load_profile(profile)
        else:
            raise TypeError(f'Expected dict, not type {type(profile)}')

        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

        self.itemChanged.connect(self.make_exclusive)
        self.itemChanged.connect(self.check_dependency)

    def contextMenu(self, event):
        """
        Create context menu for parameters.

        Reminder: LEVEL_SLOT points to items in
        """
        item = self.itemAt(event)

        if item is None:
            return None

        menu = QMenu(self)

        remove_option = None
        move_action = None
        take_item = None

        if item.data(0, LEVEL_SLOT) == 0:
            take_item = item
        elif item.data(0, LEVEL_SLOT) == 1:
            take_item = item.parent()

            remove_option = QAction('Remove option')
            remove_option.triggered.connect(lambda: self.try_del_option(take_item, item))
        elif item.data(0, LEVEL_SLOT) == 2:
            take_item = item
        else:
            # TODO: Log error, shouldn't be reached either way
            return

        add_option = QAction('Add option')
        add_option.triggered.connect(lambda: self.addOption.emit(take_item))

        if take_item.data(0, LEVEL_SLOT) != 2:
            move_action = QAction('Favorite' if not self.favorite else 'Remove favorite')
            move_action.triggered.connect(lambda: self.move_widget(take_item))
            move_action.setIconVisibleInMenu(False)

        menu.addAction(add_option)

        if remove_option:
            menu.addAction(remove_option)

        menu.addSeparator()
        menu.addAction(move_action)

        menu.exec_(QCursor.pos())

    def try_del_option(self, parent: QTreeWidgetItem, child: QTreeWidgetItem):
        self.itemRemoved.emit(parent, parent.indexOfChild(child))

    def _del_option(self, parent: QTreeWidgetItem, child: QTreeWidgetItem):

        self.blockSignals(True)

        parent.removeChild(child)
        selected_option = False
        for i in range(parent.childCount()):
            parent.child(i).setData(0, INDEX_SLOT, i)
            if parent.child(i).checkState(0) == Qt.Checked:
                selected_option = True

        if parent.childCount() > 0 and not selected_option:
            parent.child(0).setCheckState(0, Qt.Checked)

        # Deselects if no options left
        if not parent.childCount():
            parent.setCheckState(0, Qt.Unchecked)

        self.blockSignals(False)

        self.update_size()

    def move_widget(self, item: QTreeWidgetItem):
        self.blockSignals(True)
        taken_item = self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        self.blockSignals(False)
        self.move_request.emit(taken_item, self.favorite)

    def load_profile(self, profile: dict):
        self.blockSignals(True)
        self.setSortingEnabled(False)
        self.clear()

        for name, settings in profile.items():
            parent = self.make_option(name, self, settings['state'], 0, settings['tooltip'], settings['dependency'])
            if settings['options']:
                for number, choice in enumerate(settings['options']):
                    if settings['active option'] == number:
                        option = self.make_option(str(choice), parent, True, 1, subindex=number)
                        option.setFlags(option.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        option = self.make_option(str(choice), parent, False, 1, subindex=number)
            self.make_exclusive(parent)

        self.hock_dependency()
        self.update_size()
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.blockSignals(False)

    def hock_dependency(self):
        top_level_names = []

        for item in self.topLevelItems():

            # Create a list if top level items, their dependent and the QModelIndex of said item.
            top_level_names.append([item.data(0, DATA_SLOT), item.data(0, CHECKLIST_SLOT), self.indexFromItem(item)])

        # Locate matches, and store in dict
        # TODO: Make readable. THIS IS DARK MAGIC
        indices = {t[0]: i for i, t in enumerate(top_level_names)}
        for index, (first, second, third) in enumerate(top_level_names):
            if second in indices:
                # Locate matches and assign dependent reference.
                dependent = self.itemFromIndex(third)
                # Locate host (that dependent needs to have checked)
                host = self.itemFromIndex(top_level_names[indices[second]][2])

                # Check if there is a reference to other dependents.
                # If True, make add a new dependency, if not, make a list with a dependency.
                if type(host.data(0, DEPENDENT_SLOT)) is list:
                    host.setData(0, DEPENDENT_SLOT, host.data(0, DEPENDENT_SLOT) + [dependent])
                else:
                    host.setData(0, DEPENDENT_SLOT, [dependent])

        # Ensure dependents are disabled on start!
        for item in self.topLevelItems():
            self.check_dependency(item)

    def check_dependency(self, item: QTreeWidgetItem):
        """
        Looks for mentioned dependents, and enables/disables those depending on checkstate.

        :param item: changed item from QTreeWidget (paramTree)
        :type item: QTreeWidget
        """

        if item.data(0, LEVEL_SLOT) == 0 and item.data(0, DEPENDENT_SLOT):
            for i in item.data(0, DEPENDENT_SLOT):
                if item.checkState(0) == Qt.Unchecked:
                    self.blockSignals(True)
                    i.setDisabled(True)
                    i.setExpanded(False)
                    self.blockSignals(False)
                    i.setCheckState(0, Qt.Unchecked)
                else:
                    self.blockSignals(True)
                    i.setDisabled(False)
                    self.blockSignals(False)

    def topLevelItems(self):
        """Iterates through toplevelitems and returns them."""
        for i in range(self.topLevelItemCount()):
            yield self.topLevelItem(i)

    def childrens(self, item: QTreeWidgetItem):
        """Iterates through toplevelitems and returns them."""
        for i in range(item.childCount()):
            yield item.child(i)

    @staticmethod
    def make_option(name: str,
                    parent: Union[QTreeWidget, QTreeWidgetItem],
                    checkstate: bool,
                    level: int = 0,
                    tooltip: Optional[str] = None,
                    dependency: Optional[list] = None,
                    subindex: Optional[int] = None) \
            -> QTreeWidgetItem:
        """
        Makes a QWidgetItem and returns it.
        """
        if level != 1:
            widget_item = QTreeWidgetItem(parent, [name])
        else:
            widget_item = TreeWidgetItem(parent, [name])

        if tooltip:
            widget_item.setToolTip(0, tooltip)
        if checkstate:
            widget_item.setCheckState(0, Qt.Checked)
        else:
            widget_item.setCheckState(0, Qt.Unchecked)

        widget_item.setData(0, DATA_SLOT, name)
        widget_item.setData(0, LEVEL_SLOT, level)

        if level == 1:
            widget_item.setData(0, INDEX_SLOT, subindex)
        elif level == 0:
            if dependency:
                widget_item.setData(0, CHECKLIST_SLOT, dependency)

        return widget_item

    def update_size(self):
        """Sets widget size. Required to keep consistent."""
        # 15 and 20 are arbitrary units for height if each treelevelitem.
        child_size = 15 * sum(
            [1 for i in range(self.topLevelItemCount()) for _ in range(self.topLevelItem(i).childCount())])
        parent_size = 20 * self.topLevelItemCount()

        # Unhandled lengths when the program exceeds the window size. Might implement a max factor, and allow scrolling.
        if ParameterTree.max_size < (child_size + parent_size):
            self.setFixedHeight(ParameterTree.max_size)
        else:
            self.setFixedHeight((child_size + parent_size))

    def expand_options(self, item: QTreeWidgetItem):
        """Handles if the options should show, depends on checkstate."""
        if item.checkState(0) == Qt.Checked:
            item.setExpanded(True)
        else:
            item.setExpanded(False)

    def resizer(self, item: QTreeWidgetItem):
        # print('Child count', item.childCount())
        if item.checkState(0):
            if self.height() + 15 * item.childCount() < ParameterTree.max_size:
                self.setFixedHeight(self.height() + 15 * item.childCount())
            # print('Expanding')
        else:
            self.update_size()
            # print('Collapsing')

    def make_exclusive(self, item: QTreeWidgetItem):
        """
        Handles changes to self. Ensure options are expand_options, and resizes self when needed.
        """
        if self.signalsBlocked():
            unblock = False
        else:
            unblock = True

        if item.data(0, LEVEL_SLOT) == 0:
            self.expand_options(item)
            self.resizer(item)

        elif item.data(0, LEVEL_SLOT) == 1:
            self.blockSignals(True)
            for i in range(item.parent().childCount()):

                TWI = item.parent().child(i)
                try:
                    if TWI == item:
                        TWI.setFlags(TWI.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        TWI.setCheckState(0, Qt.Unchecked)
                        TWI.setFlags(TWI.flags() | Qt.ItemIsUserCheckable)
                except Exception as e:
                    # Log error
                    print(e)
        elif item.data(0, LEVEL_SLOT) == 2:
            # DEPRECATED
            pass  # Custom options should not have options, not now at least.
        else:
            pass  # TODO: Log error: state state not set.

        if unblock:
            self.blockSignals(False)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    SampleDict = {
        "Other stuff": {
            "multidl_txt": "C:/User/Mike Hunt/links.txt"
        },
        "Settings": {
            "Add thumbnail": {
                "active option": 0,
                "command": "--embed-thumbnail",
                "dependency": "Convert to audio",
                "options": None,
                "state": True,
                "tooltip": "Include thumbnail on audio files."
            },
            "Convert to audio": {
                "active option": 0,
                "command": "-x --audio-format {} --audio-quality 0",
                "dependency": None,
                "options": [
                    "mp3",
                    "mp4"
                ],
                "state": True,
                "tooltip": "Convert to selected audio format."
            },
            "Download location": {
                "active option": 2,
                "command": "-o {}",
                "dependency": None,
                "options": [
                    "D:/Music/DL/",
                    "C:/Users/Clint Oris/Downloads/",
                    "D:/Music/"
                ],
                "state": True,
                "tooltip": "Select download location."
            },
            "Ignore errors": {
                "active option": 0,
                "command": "-i",
                "dependency": None,
                "options": None,
                "state": True,
                "tooltip": "Ignores errors, and jumps to next element instead of stopping."
            },
            "Keep archive": {
                "active option": 0,
                "command": "--download-archive {}",
                "dependency": None,
                "options": [
                    "Archive.txt"
                ],
                "state": False,
                "tooltip": "Saves links to a textfile to avoid duplicates later."
            },
            "Strict file names": {
                "active option": 0,
                "command": "--restrict-filenames",
                "dependency": None,
                "options": None,
                "state": False,
                "tooltip": "Sets strict naming, to prevent unsupported characters in names."
            }
        }
    }

    app = QApplication(sys.argv)
    Checkbox = ParameterTree(SampleDict['Settings'])
    Checkbox.__name__ = 'Favorites'
    Checkbox.show()

    app.exec_()
