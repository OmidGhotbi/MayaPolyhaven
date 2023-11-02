import os
import sys
from enum import Enum
from PySide2.QtWidgets import QMainWindow, QPushButton, QProgressBar, QLineEdit, QFileDialog, QMenuBar, QMenu, QMessageBox
from PySide2.QtCore import QThread, Signal
from PySide2 import QtWidgets, QtCore, QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

basePath = 'C:/HdriHaven'
sys.path.append(basePath)
from get_path import getPath
path = getPath().get_inventory_path()
maya_modul_path = getPath().get_maya_module_path()
sys.path.append(maya_modul_path)
import requests

from set_category import getCategories
from get_data import load_data
from sync import SyncThread
from pop_menu import popbutton
from download import DownloadThread
from window import Window, maya_main_window

# Categories enum
class cat(Enum):
    HDRIs = 0
    Textures = 1
    Models = 2

# Main UI windows class
class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=maya_main_window()):
        super(Window, self).__init__(parent)
        self.setWindowTitle('Poly Haven Asset Manager')
        
        # Load the JSON data from the local file if it's available
        self.data = load_data()

        self.buttons = []

        # Create the main layout
        main_layout = QtWidgets.QGridLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.resize(830, 640)
        
        # Create a horizontal layout for the sync button and progress bar
        top_layout = QtWidgets.QHBoxLayout()
        
        # Create the sync button
        self.sync_button = QtWidgets.QPushButton(' Sync ')
        self.sync_button.clicked.connect(self.start_sync)
        top_layout.addWidget(self.sync_button)
        
        # Create the progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        top_layout.addWidget(self.progress_bar)

        # Create a button for downloading all items
        self.download_all_button = QtWidgets.QPushButton('Download All')
        top_layout.addWidget(self.download_all_button)
        
        # Add the horizontal layout to the main layout at row 0, column 1
        main_layout.addLayout(top_layout, 0, 0)
        
        # Create the splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Create the tree list
        self.tree_list = QtWidgets.QTreeWidget()
        self.tree_list.setHeaderLabels(['Categories'])
        
        # Set a maximum width for the tree list
        self.tree_list.setMaximumWidth(200)
        
        # Load categories and subcategories
        categories, nested_subcategories = getCategories().load_categories()
        
        # Add categories and subcategories to the tree list
        self.add_to_tree(categories, nested_subcategories)
        
        # Create the tab widget
        tab_widget = QtWidgets.QTabWidget()

        # Create the tab
        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setStyleSheet("background-color: #2b2b2b;")
        
        # Create a QScrollArea and set its widget to be tab1
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create the layout and set it for the scroll_widget
        self.layout1 = QtWidgets.QGridLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        
        tab_widget.addTab(scroll_area, 'Previews')

        # Initialize column count
        self.column_count = 0
        self.row_count = 0
        
        # Create a vertical layout for the right side of the window
        right_layout = QtWidgets.QVBoxLayout()
        
        # Create a combo box for the resolution options
        self.resolution_combo_box = QtWidgets.QComboBox()
        self.resolution_combo_box.addItems(['1k', '2k', '4k', '8k'])
        self.resolution_combo_box.currentTextChanged.connect(self.on_quality_changed)
        right_layout.addWidget(self.resolution_combo_box)
        
        # Create a button for downloading the selected item
        self.download_item_button = QtWidgets.QPushButton('Download')
        self.download_item_button.clicked.connect(self.download_item)
        
        # Create labels for displaying the image preview, name, category, and download status of the selected item
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        image = QtGui.QPixmap(os.path.join(basePath, "thumbnail.png"))
        image = image.scaled(135, 135, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)
        
        # Add the QLabel to your layout
        self.name_label = QtWidgets.QLabel("name")
        self.category_label = QtWidgets.QLabel("Category")
        self.download_status_label = QtWidgets.QLabel("Downloaded")

        
        # Add to layout
        right_layout.addWidget(self.image_label)
        right_layout.addWidget(self.download_item_button)
        right_layout.addWidget(self.name_label)
        right_layout.addWidget(self.category_label)
        right_layout.addWidget(self.download_status_label)
        
        # Add a stretchable spacer at the end
        right_layout.addStretch()
        
        # Create a QWidget and set its layout to right_layout
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)
        
        # Set a maximum width for the right_widget
        right_widget.setMaximumWidth(150)
        
        # Add to your main layout
        splitter.addWidget(self.tree_list)
        splitter.addWidget(tab_widget)
        splitter.addWidget(right_widget)

        # Create a menu bar with "Settings" and "About" options
        menu_bar = QMenuBar()
        
        settings_menu = QMenu("Settings", menu_bar)
        set_inventory_path_action = settings_menu.addAction("Set Inventory Path")
        set_inventory_path_action.triggered.connect(self.browse_folder)
        
        about_menu = QMenu("About", menu_bar)
        about_action = about_menu.addAction("About")
        about_action.triggered.connect(self.show_about_info)

        menu_bar.addMenu(settings_menu)
        menu_bar.addMenu(about_menu)

        # Set the menu bar of the main window
        self.setMenuBar(menu_bar)
    
    # Select new path
    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            # Update settings.json with the selected path
            getPath().update_settings(folder_path)

    # Show About window
    def show_about_info(self):
         QMessageBox.about(self, "About", "Version: v0.0.17 beta 1\nOmid Ghotbi\nomidt.gh@gmail.com")

    # Pepulate main brunch of tree view
    def add_to_tree(self, categories, nested_subcategories):
        for category in categories:
            category_item = QtWidgets.QTreeWidgetItem([category])
            self.add_items(category_item, nested_subcategories[category])
            self.tree_list.addTopLevelItem(category_item)

    # Pepulate sub item of tree view
    def add_items(self, parent_item, items):
        if isinstance(items, list):
            for item in items:
                item_widget = QtWidgets.QTreeWidgetItem([item])
                parent_item.addChild(item_widget)
        elif isinstance(items, dict):
            for item, subitems in items.items():
                item_widget = QtWidgets.QTreeWidgetItem([item])
                parent_item.addChild(item_widget)
                self.add_items(item_widget, subitems)

    # Call sync thread in backgroud
    def start_sync(self):
        self.sync_thread = SyncThread()
        self.sync_thread.progress.connect(self.update_progress)
        self.sync_thread.start()

    # Update progress bar
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # Set variables and call download thread in background
    def download_item(self):
        # Get necessary values
        quality = self.resolution_combo_box.currentText()
        name = self.name_label.text()
        categoryName = self.category_label.text()
        category = cat[categoryName]
        self.progress_bar.setValue(0)

        # Call download_item with the appropriate arguments
        self.download_thread = DownloadThread(category, name, quality)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.start()
        #download_item(category, name, quality)

    # Update lables and item preview
    def update_labels(self, i):
        path = getPath().get_inventory_path()
        # Get the button that was clicked
        button = self.layout1.itemAt(i).widget()
        name = button.objectName()
        #if self.category == cat.HDRIs.value:
        category = button.category._member_names_[button.category.value] 
    
        # Update the labels and preview
        image = QtGui.QPixmap(os.path.join(path, name, f"{name}.png"))
        image = image.scaled(135, 135, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)
        self.name_label.setText(name)
        self.category_label.setText(category)
    
    # Set quality change for items
    def on_quality_changed(self):
        new_quality = self.resolution_combo_box.currentText()
        for button in self.buttons:
            button.update_quality(new_quality)

    # Update images base on category selection
    def change_images(self, item):
        # Calculate the new number of rows and columns based on the size of the window
        new_row_count = ((self.width()-400) // 100) 
        new_column_count = self.height() // 100 
        
        path = getPath().get_inventory_path()

        # Clear the layout
        for i in reversed(range(self.layout1.count())):
            self.layout1.itemAt(i).widget().setParent(None)
    
        # Check if data is empty or None, and if so, call load_data()
        if not self.data:
            self.data = load_data()
    
        # Init variables
        images = []
        catSet = []
        nameSet = []
        setQuality = []

        # Get the images based on the selected item
        for name, info in self.data.items():
            if info['type'] == cat.HDRIs.value:
                if item.text(0) in info['categories'] and (item.parent().text(0) == 'HDRIs' or item.parent().text(0) in info['categories']):
                    image_path = os.path.join(path, name, f"{name}.png")
                    if os.path.isfile(image_path):
                        images.append(image_path)
                        catSet.append(cat.HDRIs)
                        nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                        setQuality.append(self.resolution_combo_box.currentText())
            if info['type'] == cat.Textures.value:
                if item.text(0) in info['categories'] and (item.parent().text(0) == 'Textures' or item.parent().text(0) in info['categories']):
                    image_path = os.path.join(path, name, f"{name}.png")
                    if os.path.isfile(image_path):
                        images.append(image_path)
                        catSet.append(cat.Textures)
                        nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                        setQuality.append(self.resolution_combo_box.currentText())
            elif info['type'] == cat.Models.value:
                if item.text(0) in info['categories'] and (item.parent().text(0) == 'Models' or item.parent().text(0) in info['categories']):
                    image_path = os.path.join(path, name, f"{name}.png")
                    if os.path.isfile(image_path):
                        images.append(image_path)
                        catSet.append(cat.Models)
                        nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                        setQuality.append(self.resolution_combo_box.currentText())
        
        # Define custom buttons for each item
        for i, image_path in enumerate(images):
            name = os.path.splitext(os.path.basename(image_path))[0]
            icon = QtGui.QIcon(image_path)
            #button = QtWidgets.QPushButton()
            button = popbutton(catSet[i], nameSet[i], setQuality[i], window)
            self.buttons.append(button)
            button.setObjectName(name)
            button.setIcon(icon)
            button.setStyleSheet("background-color: transparent;")# border: none;")
            button.setIconSize(QtCore.QSize(96, 96))
            button.setFixedSize(QtCore.QSize(96, 96))
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            button.setSizePolicy(sizePolicy)
            # Connect the slot to the clicked signal
            button.clicked.connect(lambda checked=False, i=i: self.update_labels(i))
            self.layout1.addWidget(button, i // new_row_count, i % new_row_count, alignment=QtCore.Qt.AlignLeft)

        # Add a stretchable empty widget at the end of the grid
        stretch_widget = QtWidgets.QWidget()
        stretch_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout1.addWidget(stretch_widget, self.layout1.rowCount(), self.layout1.rowCount())

    # Update images base on category selection if window is resized
    def resizeEvent(self, event):
        # Calculate the new number of rows and columns based on the size of the window
        new_row_count = ((self.width()-400) // 100)
        new_column_count = self.height() // 100

        path = getPath().get_inventory_path()

        # Check if column count has changed
        if new_row_count != self.row_count:
            self.row_count = new_row_count

            # Clear the existing layout
            for i in reversed(range(self.layout1.count())):
                self.layout1.itemAt(i).widget().setParent(None)

            # Init variables
            images = []
            catSet = []
            nameSet = []
            setQuality = []

            # Check if an item is selected in the tree list and get the images based on the selected item
            selected_items = self.tree_list.selectedItems()
            if selected_items:
                item = selected_items[0]
                for name, info in self.data.items():
                    if info['type'] == cat.HDRIs.value:
                        if item.text(0) in info['categories'] and (item.parent().text(0) == 'HDRIs' or item.parent().text(0) in info['categories']):
                            image_path = os.path.join(path, name, f"{name}.png")
                            if os.path.isfile(image_path):
                                images.append(image_path)
                                catSet.append(cat.HDRIs)
                                nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                                setQuality.append(self.resolution_combo_box.currentText())
                    if info['type'] == cat.Textures.value:
                        if item.text(0) in info['categories'] and (item.parent().text(0) == 'Textures' or item.parent().text(0) in info['categories']):
                            image_path = os.path.join(path, name, f"{name}.png")
                            if os.path.isfile(image_path):
                                images.append(image_path)
                                catSet.append(cat.Textures)
                                nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                                setQuality.append(self.resolution_combo_box.currentText())
                    elif info['type'] == cat.Models.value:
                        if item.text(0) in info['categories'] and (item.parent().text(0) == 'Models' or item.parent().text(0) in info['categories']):
                            image_path = os.path.join(path, name, f"{name}.png")
                            if os.path.isfile(image_path):
                                images.append(image_path)
                                catSet.append(cat.Models)
                                nameSet.append(os.path.splitext(os.path.basename(image_path))[0])
                                setQuality.append(self.resolution_combo_box.currentText())

            # Define custom buttons for each item
            for i, image_path in enumerate(images):
                name = os.path.splitext(os.path.basename(image_path))[0]
                icon = QtGui.QIcon(image_path)
                #button = QtWidgets.QPushButton()
                button = popbutton(catSet[i], nameSet[i], setQuality[i], window)
                button.setObjectName(name)
                button.setIcon(icon)
                button.setStyleSheet("background-color: transparent;")# border: none;")
                button.setIconSize(QtCore.QSize(96, 96))
                button.setFixedSize(QtCore.QSize(96, 96))
                sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                button.setSizePolicy(sizePolicy)
                # Connect the slot to the clicked signal
                button.clicked.connect(lambda checked=False, i=i: self.update_labels(i))
                self.layout1.addWidget(button, i // new_row_count, i % new_row_count, alignment=QtCore.Qt.AlignLeft)
                
        # Add a stretchable empty widget at the end of the grid
        stretch_widget = QtWidgets.QWidget()
        stretch_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout1.addWidget(stretch_widget, self.layout1.rowCount(), self.layout1.rowCount())

# define window
window = None

# Show main windows function
def show_window():
    global window
    if window is not None:
        window.close()
    window = Window()
    window.tree_list.itemClicked.connect(window.change_images)
    window.show()
