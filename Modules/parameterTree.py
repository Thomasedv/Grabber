import sys
from typing import Union, Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class ParameterTree(QTreeWidget):
    def __init__(self, dicts: dict):
        """
        Data table:
        All data is in column 0.
        --
        0  - Visual name.
        32 - main data entry, name of parents, full data for children
        33 - 0 for parent, 1 for children, 3 for custom option.
        34 - Name of item that needs to be checked
        35 - index for children used for active option
        37 - List of QModelIndex to items that this depends on.

        """
        super().__init__()

        self.setExpandsOnDoubleClick(False)
        # self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setHeaderHidden(True)
        # self.header().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        # self.headerItem().setResizeMode(QHeaderView.ResizeToContents)

        # self.setItemWidget()
        for name, settings in dicts.items():
            parent = self.make_option(name, self, settings['state'], 0, settings['tooltip'], settings['dependency'])
            if settings['options'] is not None:
                for number, choice in enumerate(settings['options']):
                    if settings['Active option'] == number:
                        option = self.make_option(choice, parent, True, 1, subindex=number)
                        option.setFlags(option.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        option = self.make_option(choice, parent, False, 1, subindex=number)
            self.make_exclusive(parent)

        self.hock_dependency()

        self.itemChanged.connect(self.make_exclusive)
        self.itemChanged.connect(self.check_dependency)

        self.start_size()

    def hock_dependency(self):
        top_level_names = []
        for item in self.topLevelItems():
            # Create a list if top level items, their dependent and the QModelIndex of said item.
            top_level_names.append([item.data(0, 32), item.data(0, 34), self.indexFromItem(item)])

        # Locate matches, and store in dict

        indices = {t[0]: i for i, t in enumerate(top_level_names)}
        for index, (first, second, third) in enumerate(top_level_names):
            if second in indices:
                # Locate matches and assign dependent reference.
                dependent = self.itemFromIndex(third)
                # Locate host (that dependent needs to have checked)
                host = self.itemFromIndex(top_level_names[indices[second]][2])

                # Check if there is a reference to other dependents.
                # If True, make add a new dependency, if not, make a list with a dependency.
                if type(host.data(0, 37)) is list:
                    host.setData(0, 37, host.data(0, 37) + [dependent])
                else:
                    host.setData(0, 37, [dependent])

        # Ensure dependents are disabled on start!
        for item in self.topLevelItems():
            self.check_dependency(item)

    def check_dependency(self, item: QTreeWidgetItem):
        """
        Looks for mentioned dependents, and enables/disables those depending on checkstate.

        :param item: changed item from QTreeWidget (paramTree)
        :type item: QTreeWidget
        """
        if item.data(0, 33) == 0 and item.data(0, 37):
            for i in item.data(0, 37):
                if item.checkState(0) == Qt.Unchecked:
                    self.blockSignals(True)
                    i.setDisabled(True)
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
                    subindex: Optional[int] = None)\
            -> QTreeWidgetItem:
        """
        Makes a QWidgetItem and returns it.
        """
        widget_item = QTreeWidgetItem(parent, [name])
        if tooltip:
            widget_item.setToolTip(0, tooltip)
        if checkstate:
            widget_item.setCheckState(0, Qt.Checked)
        else:
            widget_item.setCheckState(0, Qt.Unchecked)

        widget_item.setData(0, 32, name)
        widget_item.setData(0, 33, level)

        if level == 1:
            widget_item.setData(0, 35, subindex)
        elif level == 0:
            if dependency:
                widget_item.setData(0, 34, dependency)

        return widget_item

    def start_size(self):
        """Sets widget size. Required to keep consistent."""
        size = sum([1 for i in range(self.topLevelItemCount()) for _ in range(self.topLevelItem(i).childCount())])
        # Unhandled lengths when the program exceeds the window size. Might implement a max factor, and allow scrolling.
        # Future cases might implement two ParameterTrees side by side, for better use of space and usability.
        self.setFixedHeight(20 * self.topLevelItemCount() + 15 * size)

    def expand_options(self, item: QTreeWidgetItem):
        """Handles if the options should show, depends on checkstate."""
        if item.checkState(0) == Qt.Checked:
            item.setExpanded(True)
        else:
            item.setExpanded(False)

    def resizer(self, item: QTreeWidgetItem):
        # print('Child count', item.childCount())
        if item.checkState(0):
            self.setFixedHeight(self.height() + 15 * item.childCount())
            # print('Expanding')
        else:
            self.setFixedHeight(self.height() - 15 * item.childCount())
            # print('Collapsing')

    def make_exclusive(self, item: QTreeWidgetItem):
        """
        Handles changes to self. Ensure options are expand_options, and resizes self when needed.
        """
        if item.data(0, 33) == 0:
            self.expand_options(item)
            self.resizer(item)
            # print('item is parent box')
        elif item.data(0, 33) == 1:
            self.blockSignals(True)
            for i in range(item.parent().childCount()):
                # print(type(self.itemFromIndex(i)))
                TWI = item.parent().child(i)
                try:
                    if TWI == item:
                        TWI.setFlags(TWI.flags() ^ Qt.ItemIsUserCheckable)
                        # print('Skipping self')
                    else:
                        # print('Unchecking')
                        TWI.setCheckState(0, Qt.Unchecked)
                        TWI.setFlags(TWI.flags() | Qt.ItemIsUserCheckable)
                except Exception as e:
                    print(e)
        elif item.data(0, 33) == 2:
            pass  # Custom options should not have options, not now at least.
        else:
            print('Parent/child state not set.' + str(item.data(0, 32)))
        self.blockSignals(False)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    SampleDict = {
    "Other stuff": {
        "multidl_txt": "C:/User/Mike Hunt/links.txt"
    },
    "Settings": {
        "Add thumbnail": {
            "Active option": 0,
            "Command": "--embed-thumbnail",
            "dependency": "Convert to audio",
            "options": None,
            "state": True,
            "tooltip": "Include thumbnail on audio files."
        },
        "Convert to audio": {
            "Active option": 0,
            "Command": "-x --audio-format {} --audio-quality 0",
            "dependency": None,
            "options": [
                "mp3",
                "mp4"
            ],
            "state": True,
            "tooltip": "Convert to selected audio format."
        },
        "Download location": {
            "Active option": 2,
            "Command": "-o {}",
            "dependency": None,
            "options": [
                "D:/Music/DL/%(title)s.%(ext)s",
                "C:/Users/Clint Oris/Downloads/%(title)s.%(ext)s",
                "D:/Music/%(title)s.%(ext)s"
            ],
            "state": True,
            "tooltip": "Select download location."
        },
        "Ignore errors": {
            "Active option": 0,
            "Command": "-i",
            "dependency": None,
            "options": None,
            "state": True,
            "tooltip": "Ignores errors, and jumps to next element instead of stopping."
        },
        "Keep archive": {
            "Active option": 0,
            "Command": "--download-archive {}",
            "dependency": None,
            "options": [
                "Archive.txt"
            ],
            "state": False,
            "tooltip": "Saves links to a textfile to avoid duplicates later."
        },
        "Strict file names": {
            "Active option": 0,
            "Command": "--restrict-filenames",
            "dependency": None,
            "options": None,
            "state": False,
            "tooltip": "Sets strict naming, to prevent unsupported characters in names."
        }
    }
    }

    app = QApplication(sys.argv)
    Checkbox = ParameterTree(SampleDict['Settings'])
    Checkbox.show()

    app.exec_()

