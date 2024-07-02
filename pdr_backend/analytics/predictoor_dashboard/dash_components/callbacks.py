from dash import Input, Output


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(Output("file-data", "data"), Input("data-folder", "data"))
    def read_from_file(data):
        files_dir = data
        print(files_dir)
        # data = read_files_from_directory(files_dir)

        return data
