SENSOR_CONFIG = [
    {
        "id": "packet_isolation",
        "name": "Packet Isolation Detection",
        "ports": [5000, 5001],
        "data_slice": [3],
        "csv_file": "packet_strength.csv",
        "csv_columns": ["in_temp", "in_pressure", "in_humidity", "out_temp", "out_pressure", "out_humidity"]
        ,"Port_Labels": [["Inside Temperature", "Inside Pressure", "Inside Humidity"], ["Outside Temperature", "Outside Pressure", "Outside Humidity"]]
    },
    {
        "id": "photosensitivity",
        "name": "PhotoSensitivity Detection System",
        "ports": [5002],
        "data_slice": [4],
        "csv_file": "photosensitivity.csv",
        "csv_columns": ["R_VALUE", "G_VALUE", "B_VALUE", "Detection_Value"],
        "Port_Labels": ["R Value", "G Value", "B Value", "Detection Value"]
    },{
        "id": "RFID",
        "name": "RFID Warehousing System",
        "ports": [5003],
        "data_slice": [3],
        "csv_file": "RFID.csv",
        "csv_columns": ["UID", "alloted_ID", "location"],
        "Port_Labels": ["UID", "Alotted ID", "location"]
    },{
        "id": "Soil",
        "name": "Soil Moisture Detection System",
        "ports": [5004],
        "data_slice": [3],
        "csv_file": "Soil.csv",
        "csv_columns": ["Moisture_percent"],
        "Port_Labels": ["Moisture Percentage"]
    },
        
]