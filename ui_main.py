import json
from PyQt5 import QtWidgets, QtCore
import pandas as pd
import os
import socket
import subprocess

with open('config.json', 'r',encoding='utf-8') as f:
    config = json.load(f)
    f.close()   

class FiltersWidget(QtWidgets.QWidget):
    def __init__(self, tree_widget_parameters: list):
        
        super(FiltersWidget, self).__init__()
        
        self.setMinimumSize(500, 350)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.parameters_tree = QtWidgets.QTreeWidget(self)
        self.parameters_tree.setMinimumSize(450, 250)
        main_layout.addWidget(self.parameters_tree, 0, 0)

        buttons_widget = QtWidgets.QWidget(self)
        buttons_widget_layout = QtWidgets.QGridLayout(buttons_widget)
        buttons_widget_layout.setContentsMargins(0, 0, 0, 0)

        spacer = QtWidgets.QSpacerItem(360, 10)
        buttons_widget_layout.addItem(spacer, 0, 0)

        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setText("Save")
        self.save_button.setMinimumSize(70, 25)
        buttons_widget_layout.addWidget(self.save_button, 0, 1)

        self.reset_button = QtWidgets.QPushButton(self)
        self.reset_button.setText("Reset")
        self.reset_button.setMinimumSize(70, 25)
        buttons_widget_layout.addWidget(self.reset_button, 0, 2)
        main_layout.addWidget(buttons_widget, 1, 0)

        self.init_interactivities(tree_widget_parameters)
        


    def init_interactivities(self, tree_widget_parameters:dict):

        self.selected_filters = {}
        self.tree_widget_parameters = tree_widget_parameters

        self.fill_tree_widget(tree_widget_parameters)
        
        self.setup_connections()


    def fill_tree_widget(self, data:dict):
        def fill_level(parent, childs_list):
            for child in childs_list:
                tree_widget_item = QtWidgets.QTreeWidgetItem(parent)
                tree_widget_item.setText(0, child)
                if child!='side' and child!='no_trade' and child!='processing_result' and child!="endpoint":
                    tree_widget_item.setFlags(tree_widget_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    tree_widget_item.setCheckState(0, QtCore.Qt.Unchecked)
                
                if type(childs_list[child]) == dict:
                        fill_level(tree_widget_item, childs_list[child])
                if type(childs_list[child]) == list:
                    for element in childs_list[child]:
                        element_tree_widget_item = QtWidgets.QTreeWidgetItem(tree_widget_item)
                        if element != "side" and element != "no_trade" and element!="processing_result" and element!="endpoint":   
                            element_tree_widget_item.setFlags(element_tree_widget_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                            element_tree_widget_item.setCheckState(0, QtCore.Qt.Unchecked)
                        element_tree_widget_item.setText(0, element)

        fill_level(self.parameters_tree, data)


    def handler(self, element, column):

        parent = element.parent()
        if parent == None:
            parameter_name = "bot_id"
        else:
            parameter_name = str(parent.text(0))
        parameter_value = str(element.text(0))

        if parameter_name == "bot_id":
            parameter_name = "Bot_ID"
        if parameter_name == "incoming":
            parameter_name = "Incoming"
        if parameter_name == "processing_result":
            parameter_name = "Processing_Result"
        if parameter_name == "side":
            parameter_name = "Incoming"
        if parameter_name == "no_trade":
            parameter_name = "Incoming"
        if parameter_name == "endpoint":
            parameter_name = "Endpoint"

        if parameter_name not in self.selected_filters:
            self.selected_filters[parameter_name]=[]
            self.selected_filters[parameter_name].append(parameter_value)
            return None

        if parameter_name in self.selected_filters:

            if parameter_value in self.selected_filters[parameter_name]:
                self.selected_filters[parameter_name].remove(parameter_value)
                if len(self.selected_filters[parameter_name]) == 0:
                    self.selected_filters.pop(parameter_name)
                return None
            
            if parameter_value not in self.selected_filters[parameter_name]:
                self.selected_filters[parameter_name].append(parameter_value)
                return None
        

    def apply(self):
        result = ""

        for parameter_name in self.selected_filters:
            if parameter_name == "bot_id":
                parameter_name = "Bot_ID"
            if parameter_name == "incoming":
                parameter_name = "Incoming"
            if parameter_name == "processing_result":
                parameter_name = "Processing_Result"
            if parameter_name == "side":
                parameter_name = "Incoming"
            if parameter_name == "no_trade":
                parameter_name = "Incoming"
            if parameter_name == "endpoint":
                parameter_name = "Endpoint"
             
            current_parameter_values = ""
            for parameter_value in self.selected_filters[parameter_name]:    
                if len(current_parameter_values) == 0: 
                    current_value = "{}=='{}'".format(parameter_name.replace(" ", ""), parameter_value)
                else:
                    current_value = "or {}=='{}'".format(parameter_name.replace(" ", ""), parameter_value)
                current_parameter_values += current_value


            if len(result) == 0:
                result = "{}".format(current_parameter_values)
            else:
                result += "and {}".format(current_parameter_values)

        return result
            
    def setup_connections(self):
        self.parameters_tree.itemChanged.connect(self.handler)

class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        
    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def setData(self, data):
        self._data = data
        self.layoutChanged.emit()

class DashboardTableWidget(QtWidgets.QTableView):
    def __init__(self) -> None:

        super(DashboardTableWidget, self).__init__()
        
        columns = ["Date/Time", "Bot_ID", "Incoming", "Processing_Result", "Message", "Endpoint"]
        data = pd.DataFrame(columns=columns)
        self.current_filters = ""

        self.model = TableModel(data)
        self.filter_proxy_model = QtCore.QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(0)
        
        self.setModel(self.filter_proxy_model)
        
        self.verticalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionsMovable(True)
        
        self.current_table_data = None
        self.fill_table(limit=100)

    def row_count(self, parent=None) -> int:
        return len(self._data.values)

    def column_count(self, parent=None) -> int:
        return self._data.columns.size

    def fill_table(self, limit:int) -> None:

        with open('data.json', 'r',encoding='utf-8') as f:
            data = json.load(f)
            f.close()

        shaped_data = []
        limit_counter = 0
        for bot_id in data:
            if limit_counter == limit:
                break
            data[bot_id].reverse()
            for parameters_group in data[bot_id]:
                message = ""
                date_time = ""
                endpoint = ""
                if "endpoint" in parameters_group:
                    endpoint = parameters_group["endpoint"]
                if "side" in parameters_group:
                    side = parameters_group["side"]
                if "date_time" in parameters_group:
                    date_time = parameters_group["date_time"]
                processing_result = parameters_group["processing_result"]
                
                if "no_trade" in parameters_group:
                    if parameters_group["no_trade"] == "true":
                        incoming_string = "no trade"
                else:
                    incoming_string = side
                if "Keys" in parameters_group:
                    message = parameters_group["Keys"]
                
                       
                shaped_data.append([date_time, bot_id, incoming_string, processing_result, message, endpoint])
                limit_counter+=1
        pdata = pd.DataFrame(shaped_data, columns = ["Date/Time", "Bot_ID", "Incoming", "Processing_Result", "Message", "Endpoint"])
        if self.current_filters != "":
            pdata = pdata.query(self.current_filters)
            
        pdata = pdata.sort_values(by="Date/Time", ascending=False)
        self.model.setData(pdata)
        self.current_table_data = pdata

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
    

class DataStatWidget(QtWidgets.QWidget):
    def __init__(self):

        super(DataStatWidget, self).__init__()

        self.setMinimumSize(350, 200)
        self.setMaximumSize(500, 200)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(0, 10, 10, 10)
        main_layout.setSpacing(10)

        self.cache_size_label = QtWidgets.QLabel(self)
        self.cache_size_label.setText("Cache Size")
        self.cache_size_label.setAlignment(QtCore.Qt.AlignCenter)
        self.cache_size_label.setMinimumSize(90, 25)
        main_layout.addWidget(self.cache_size_label, 0, 0)

        self.cache_size_value_label = QtWidgets.QLabel(self)
        self.cache_size_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.cache_size_value_label.setMinimumSize(80, 25)
        main_layout.addWidget(self.cache_size_value_label, 0, 1)

        self.cache_reset_button = QtWidgets.QPushButton(self)
        self.cache_reset_button.setText("Reset Cache")
        self.cache_reset_button.setMinimumSize(150, 25)
        main_layout.addWidget(self.cache_reset_button, 0, 2)

        self.logs_size_label = QtWidgets.QLabel(self)
        self.logs_size_label.setText("logs Size")
        self.logs_size_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logs_size_label.setMinimumSize(90, 25)
        main_layout.addWidget(self.logs_size_label, 1, 0)

        self.logs_size_value_label = QtWidgets.QLabel(self)
        self.logs_size_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logs_size_value_label.setMinimumSize(80, 25)
        main_layout.addWidget(self.logs_size_value_label, 1, 1)

        self.logs_reset_button = QtWidgets.QPushButton(self)
        self.logs_reset_button.setText("Reset logs")
        self.logs_reset_button.setMinimumSize(150, 25)
        main_layout.addWidget(self.logs_reset_button, 1, 2)


        self.records_limit_label = QtWidgets.QLabel(self)
        self.records_limit_label.setAlignment(QtCore.Qt.AlignCenter)
        self.records_limit_label.setText("Records Limit")
        self.records_limit_label.setMinimumSize(80, 25)
        main_layout.addWidget(self.records_limit_label, 2, 0)

        self.records_limit_line_edit = QtWidgets.QLineEdit(self)
        self.records_limit_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.records_limit_line_edit.setMinimumSize(80, 25)
        main_layout.addWidget(self.records_limit_line_edit, 2, 1)

        self.records_limit_save_button = QtWidgets.QPushButton(self)
        self.records_limit_save_button.setText("Save Limit")
        self.records_limit_save_button.setMinimumSize(150, 25)
        main_layout.addWidget(self.records_limit_save_button, 2, 2)

        self.setup_connections()

    def set_data(self):
        def convert_bytes(num):
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if num < 1024.0:
                    return "%3.1f %s" % (num, x)
                num /= 1024.0

        def file_size(file_path):
            """
            this function will return the file size
            """
            if os.path.isfile(file_path):
                file_info = os.stat(file_path)
                return convert_bytes(file_info.st_size)
        
        cache_size = file_size("data.json")
        logs_size = file_size("tradingviewrepeater.log")

        self.cache_size_value_label.setText(cache_size)
        self.logs_size_value_label.setText(logs_size)

    def setup_connections(self):
        def reset_cache():
            with open('data.json', 'w',encoding='utf-8') as f:
                data = {}
                json.dump(data, f)
                f.close()
        self.cache_reset_button.clicked.connect(reset_cache)

        def reset_logs():
            if os.path.isfile("tradingviewrepeater.log"):
                os.remove("tradingviewrepeater.log")
        self.logs_reset_button.clicked.connect(reset_logs)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.set_data)
        self.timer.start(200)


class ConfigSetupWidget(QtWidgets.QWidget):
    def __init__(self, parameters_names):

        super(ConfigSetupWidget, self).__init__()

        self.setMinimumSize(500, 300)
        self.setMaximumSize(166672, 400)

        main_layout = QtWidgets.QGridLayout(self)

        self.parameters_list = {}
        row = int

        with open('config.json', 'r',encoding='utf-8') as f:
            data = json.load(f)
            f.close()

        for i in range(0, len(parameters_names)):
            row = i

            parameter_name = parameters_names[i]

            parameter_name_label = QtWidgets.QLabel(self)
            parameter_name_label.setText(parameter_name)
            parameter_name_label.setMinimumSize(150, 25)
            main_layout.addWidget(parameter_name_label, i, 0)

            parameter_line_edit = QtWidgets.QLineEdit(self)
            parameter_line_edit.setText(data[parameter_name])
            parameter_line_edit.setMinimumSize(120, 25)
            main_layout.addWidget(parameter_line_edit, i, 1)

            self.parameters_list[parameter_name] = parameter_line_edit

        buttons_widget = QtWidgets.QWidget(self)
        buttons_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        buttons_widget_layout = QtWidgets.QGridLayout(buttons_widget)

        spacer = QtWidgets.QSpacerItem(120, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        buttons_widget_layout.addItem(spacer, 0, 0)

        self.save_parameters_button = QtWidgets.QPushButton(buttons_widget)
        self.save_parameters_button.setText("Save")
        self.save_parameters_button.setMinimumSize(50, 20)
        buttons_widget_layout.addWidget(self.save_parameters_button, 0, 1)

        main_layout.addWidget(buttons_widget, row+1, 1)

    def save_parameters_to_config(self):
        with open('config.json', 'r',encoding='utf-8') as f:
                data = json.load(f)
                f.close()

        for parameter_name in self.parameters_list:
            parameter_value = self.parameters_list[parameter_name].text()
            if parameter_value != "":
                data[parameter_name]=parameter_value

        with open('config.json', 'w',encoding='utf-8') as f:
                json.dump(data, f)
                f.close()
            
class MenuBar(QtWidgets.QMenuBar):
    def __init__(self):

        super(MenuBar, self).__init__()

        self.setMinimumSize(QtCore.QSize(750, 30))

        self.setup_config_action = QtWidgets.QAction(self)
        self.setup_config_action.setText("Setup Config")
        self.addAction(self.setup_config_action)

        self.app_data_action = QtWidgets.QAction(self)
        self.app_data_action.setText("App Data")
        self.addAction(self.app_data_action)


class UiMainWindow(QtWidgets.QMainWindow):
    def __init__(self):

        super(UiMainWindow, self).__init__()

        self.resize(1400, 800)
        self.setWindowTitle("Repeater Dashboard")

        self.menu_bar = MenuBar()
        self.setMenuBar(self.menu_bar)

        central_widget = QtWidgets.QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        central_widget_layout = QtWidgets.QGridLayout(central_widget)
        central_widget_layout.setContentsMargins(10, 10, 10, 5)
        central_widget_layout.setSpacing(10)


        all_filters_widget = QtWidgets.QWidget(self)
        all_filters_layout = QtWidgets.QGridLayout(all_filters_widget)
        all_filters_layout.setContentsMargins(0, 0, 0, 0)
        all_filters_layout.setSpacing(10)

        self.filters_button = QtWidgets.QPushButton(all_filters_widget)
        self.filters_button.setMinimumSize(100, 20)
        self.filters_button.setMinimumSize(100, 20)
        self.filters_button.setText("Filters")
        all_filters_layout.addWidget(self.filters_button, 0, 0)

        self.search_line = QtWidgets.QLineEdit(all_filters_widget)
        self.search_line.setMinimumSize(160, 20)
        all_filters_layout.addWidget(self.search_line, 0, 1)

        search_line_spacer = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        all_filters_layout.addItem(search_line_spacer, 0, 2)

        self.server_state_label = QtWidgets.QLabel(all_filters_widget)
        self.server_state_label.setMinimumSize(80, 25)
        all_filters_layout.addWidget(self.server_state_label, 0, 3)

        central_widget_layout.addWidget(all_filters_widget, 0, 0)


        self.dashboard_table_widget = DashboardTableWidget()
        self.dashboard_table_widget.setMinimumSize(700, 350)
        central_widget_layout.addWidget(self.dashboard_table_widget, 1, 0)


        buttons_widget = QtWidgets.QWidget(central_widget)
        buttons_widget_layout = QtWidgets.QGridLayout(buttons_widget)
        buttons_widget_layout.setSpacing(10)

        spacer = QtWidgets.QSpacerItem(120, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        buttons_widget_layout.addItem(spacer, 0, 0)

        self.auto_udate_state_checkbox = QtWidgets.QCheckBox(buttons_widget)
        self.auto_udate_state_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.auto_udate_state_checkbox.setText("Auto Update")
        self.auto_udate_state_checkbox.setMinimumSize(100, 25)
        buttons_widget_layout.addWidget(self.auto_udate_state_checkbox, 0, 2)

        lower_spacer = QtWidgets.QSpacerItem(120, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        buttons_widget_layout.addItem(lower_spacer, 1, 0)

        self.alerts_counter_label = QtWidgets.QLabel(buttons_widget)
        self.alerts_counter_label.setMinimumSize(150, 25)
        self.alerts_counter_label.setText("Alerts Count:")
        buttons_widget_layout.addWidget(self.alerts_counter_label, 1, 1)
        
        self.update_button = QtWidgets.QPushButton(buttons_widget)
        self.update_button.setMinimumSize(100, 25)
        self.update_button.setText("Update Table")
        buttons_widget_layout.addWidget(self.update_button, 1, 2)

        central_widget_layout.addWidget(buttons_widget, 2, 0)

        self.filters_widget = None
        self.setup_connectins()
        self.records_limit = 100
        self.auto_update_state = False

    def setup_connectins(self):
        self.update_button.clicked.connect(lambda: self.dashboard_table_widget.fill_table(limit=self.records_limit))
        
        config_setup_widget = None
        def show_config_setup_widget():
            nonlocal config_setup_widget
            config_setup_widget = ConfigSetupWidget(["server_host", "server_port", "interpretier_path", "main.py_path"])
            config_setup_widget.show()
            config_setup_widget.save_parameters_button.clicked.connect(close_config_setup_widget)

        def close_config_setup_widget():
            config_setup_widget.save_parameters_to_config()
            config_setup_widget.close()
        
        app_data_widget = None
        def show_app_data_widget():
            nonlocal app_data_widget
            app_data_widget = DataStatWidget()
            app_data_widget.show()
            app_data_widget.records_limit_line_edit.setText(str(self.records_limit))

            def set_limit():
                limit = app_data_widget.records_limit_line_edit.text()
                if limit != '':
                    self.records_limit = int(limit)
                else:
                    limit = 100

            app_data_widget.records_limit_save_button.clicked.connect(set_limit)


        self.menu_bar.setup_config_action.triggered.connect(show_config_setup_widget)
        self.menu_bar.app_data_action.triggered.connect(show_app_data_widget)
    
            
        def show_filters_widget():
            def reset_table_filters():
                self.filters_widget.close()
                self.dashboard_table_widget.current_filters = ""
                self.filters_widget = None
                self.dashboard_table_widget.fill_table(limit=self.records_limit)
        
            def set_table_filters():
                    self.filters_widget.close()
                    self.dashboard_table_widget.current_filters = self.filters_widget.apply() 
                    self.dashboard_table_widget.fill_table(limit=self.records_limit)

            filtered_parameters = {}

            if not self.dashboard_table_widget.current_table_data is None:
                for bot_id in self.dashboard_table_widget.current_table_data["Bot_ID"].tolist():
                    filtered_endpoints = []
                    endpoints_list = self.dashboard_table_widget.current_table_data["Endpoint"].tolist()
                    for endpoint in endpoints_list:
                        
                        if endpoint != "":
                            filtered_endpoints.append(endpoint)
                    if filtered_endpoints != []:
                        filtered_parameters[bot_id] = {"side":["long", "short"], "no_trade":["true"], "processing_result":["sent", "passed"], "endpoint":filtered_endpoints}
                    else:
                        filtered_parameters[bot_id] = {"side":["long", "short"], "no_trade":["true"], "processing_result":["sent", "passed"]}

                print("Current filters - ", self.dashboard_table_widget.current_filters, " Data Table - ", self.dashboard_table_widget.current_table_data)
            
            if self.filters_widget is None:
                self.filters_widget = FiltersWidget(filtered_parameters)
                self.filters_widget.save_button.clicked.connect(set_table_filters)
                self.filters_widget.reset_button.clicked.connect(reset_table_filters)

            self.filters_widget.show()
            
        self.filters_button.clicked.connect(show_filters_widget)
        self.search_line.textChanged.connect(self.dashboard_table_widget.filter_proxy_model.setFilterRegExp)

        def set_server_status():
            state = ""

            with open("data.json", "r") as f:
                data = json.load(f)
                alerts_count = 0
                for bot_id in data:
                    for alert in data[bot_id]:
                        alerts_count += 1
                
                self.alerts_counter_label.setText("Alerts Count:  " + str(alerts_count))
                

            if self.auto_udate_state_checkbox.isChecked() == True:
                self.dashboard_table_widget.fill_table(self.records_limit)
    
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
                test_socket.bind((config["server_host"], int(config["server_port"])))
            except socket.error:
                state = "Active"
                self.server_state_label.setText("Active")
            finally:
                if state != "Active" or state == "":
                    self.server_state_label.setText("Disabled")
                    retcode = subprocess.call([config["interpretier_path"], config["main.py_path"]])
                    
        self.server_state_timer = QtCore.QTimer(self)
        self.server_state_timer.timeout.connect(set_server_status)
        self.server_state_timer.start(5000)

def setup_app_style(app):
    with open('stylesheet.qss','r') as f:
        style = f.read()
        f.close()

    app.setStyleSheet(style)

if __name__ == "__main__":

    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = UiMainWindow() 
    
    setup_app_style(app)

    main_window.show()
    sys.exit(app.exec_())