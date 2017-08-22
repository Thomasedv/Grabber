import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class paramTree(QTreeWidget):
    def __init__(self, dicts: dict):
        super().__init__()
        """
        data table:
        All data is in row 0. 
        --
        0  -
        32 - main data entry, name of parents, full data for children
        33 - 0 for parent, 1 for children
        34 - Name of item that needs to be checked
        35 - index for children used for active option
        37 - List of QModelIndex to items that this depends on.

        """
        self.setExpandsOnDoubleClick(False)
        # self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setHeaderHidden(True)
        # self.header().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        # self.headerItem().setResizeMode(QHeaderView.ResizeToContents)

        # self.setItemWidget()
        for name, settings in dicts.items():
            parent = self.makeOption(name, self, settings['state'], 0, settings['tooltip'], settings['dependency'])
            if settings['options'] is not None:
                for number, choice in enumerate(settings['options']):
                    if settings['Active option'] == number:
                        sub = self.makeOption(choice, parent, True, 1, subindex=number)
                        sub.setFlags(sub.flags() ^ Qt.ItemIsUserCheckable)
                    else:
                        sub = self.makeOption(choice, parent, False, 1, subindex=number)
            self.makeExclusive(parent)

        self.hockDependecy()
        self.itemChanged.connect(self.makeExclusive)
        self.itemChanged.connect(self.checkDependecny)
        self.startSize()

    def hockDependecy(self):
        toplevelnames = []
        for i in self.topLevelItems():
            # Create a list if top level items, their dependent and the QModelIndex of said item.
            toplevelnames.append([i.data(0, 32), i.data(0, 34), self.indexFromItem(i)])
        # Locate matches, and store in dict
        indices = {t[0]: i for i, t in enumerate(toplevelnames)}
        for index, (first, second, third) in enumerate(toplevelnames):
            if second in indices:
                # Locate matches and assign dependent reference.
                dependent = self.itemFromIndex(third)
                # Locate host (that dependent needs to have checked)
                host = self.itemFromIndex(toplevelnames[indices[second]][2])

                # Check if there is a reference to other dependents.
                # If True, make add a new dependency, if not, make a list with a dependency.
                if type(host.data(0, 37)) is list:
                    host.setData(0, 37, host.data(0, 37) + [dependent])
                else:
                    host.setData(0, 37, [dependent])
        # Ensure dependents are disabled on start!
        for item in self.topLevelItems():
            self.checkDependecny(item)

    def checkDependecny(self, item: QTreeWidgetItem):
        """
        Looks for mentioned dependents, and enables/disables those depending on chekcstate.

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
        for i in range(self.topLevelItemCount()):
            yield self.topLevelItem(i)

    @staticmethod
    def makeOption(name, parent, checkstate, level=0, tooltip=None, dependency=None, subindex=None):
        # implemter data 33 for parent/child.
        #
        # print(name)
        mainItem = QTreeWidgetItem(parent, [name])
        if tooltip:
            mainItem.setToolTip(0, tooltip)
        if checkstate:
            mainItem.setCheckState(0, Qt.Checked)
        else:
            mainItem.setCheckState(0, Qt.Unchecked)

        mainItem.setData(0, 32, name)
        mainItem.setData(0, 33, level)

        if level == 1:
            mainItem.setData(0, 35, subindex)
        elif level == 0:
            if dependency:
                mainItem.setData(0, 34, dependency)
        # mainItem.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)
        # mainItem.setExpanded(True)

        return mainItem

    def startSize(self):
        size = sum([1 for i in range(self.topLevelItemCount()) for x in range(self.topLevelItem(i).childCount())])
        # print(size)
        self.setFixedHeight(20 * self.topLevelItemCount() + 15 * size)

    def exclusive(self, item: QTreeWidgetItem):
        if item.checkState(0) == Qt.Checked:
            item.setExpanded(True)
        else:
            item.setExpanded(False)

    def resizer(self, item: QTreeWidgetItem):
        try:
            # print('Child count', item.childCount())
            if item.checkState(0):
                self.setFixedHeight(self.height() + 15 * item.childCount())
                # print('Expanding')
            else:
                self.setFixedHeight(self.height() - 15 * item.childCount())
                # print('Collapsing')
        except Exception as e:
            print(e)

    def makeExclusive(self, item: QTreeWidgetItem):
        # print(type(item), type(test))
        # print(type(item.checkState()))
        # if item.checkState() ==
        if item.data(0, 33) == 0:
            self.exclusive(item)
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
        else:
            print('Parent/child state not set.')
        self.blockSignals(False)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    SampleDict = {
    "Other stuff": {
        "multidl_txt": "C:/Users/THOMAS/PycharmProjects/YTDLGUI/test.txt"
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
                "D:/Musikk/DLs/%(title)s.%(ext)s",
                "C:/Users/THOMAS/Downloads/Convertering/%(title)s.%(ext)s",
                "D:/Musikk/Needs review and selection/%(title)s.%(ext)s"
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
    Checkbox = paramTree(SampleDict['Settings'])
    Checkbox.show()

    app.exec_()

