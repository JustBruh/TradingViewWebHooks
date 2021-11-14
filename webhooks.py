import os
import click
import simplejson as json

@click.group()
def cli():
    pass

@click.command(
    'status',
    help="Return current server status"
)
def get_server_status():
    status = os.system("sudo systemctl is-active webhooks.service") 
    

@click.command(
    'start',
    help="Start the server if it isn't running"
)
def start_server():
    status = os.system("sudo systemctl start webhooks.service")

@click.command(
    'stop',
    help="Stop the server if it is running"
)
def stop_server():
    status = os.system("sudo systemctl stop webhooks.service")
        
@click.command(
    'app-data',
    help="Return cache and logs size"
)
def get_app_data_size():
    def convert_bytes(num):
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if num < 1024.0:
                    return "%3.1f %s" % (num, x)
                num /= 1024.0

    def file_size(file_path):
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            return convert_bytes(file_info.st_size)

    result = ""
    for file_path in ["main.log", "ui_main.log", "data.json"]:
        size = file_size(file_path)
        result += file_path + " " + " " + size + " | "
    click.echo(result)

@click.command(
    'rc',
    help="Reset cache - data.json. The server must be stopped"
)
def reset_cache():
    click.echo("Server status:")
    status = os.system("sudo systemctl is-active webhooks.service")
    if status == 0:
        click.echo("Stop the server first!")
    else:
        with open('data.json', 'w',encoding='utf-8') as f:
            data = {}
            json.dump(data, f)
            f.close()
            click.echo("Done")

@click.command(
    'rl',
    help="Reset logs - main.log and ui_main.log"
)
def reset_logs():
        if os.path.isfile("main.log"):
            os.remove("main.log")
        if os.path.isfile("ui_main.log"):
            os.remove("ui_main.log")

@click.command(
    'a',
    help="Returns the number of alerts received"
)
def get_alerts_count():
    with open("data.json", "r") as f:
        data = json.load(f)
        f.close()

        alerts_count = 0
        for bot_id in data:
            for alert in data[bot_id]:
                alerts_count += 1
    click.echo(alerts_count)

cli.add_command(get_server_status)
cli.add_command(start_server)
cli.add_command(stop_server)
cli.add_command(get_app_data_size)
cli.add_command(reset_cache)
cli.add_command(reset_logs)
cli.add_command(get_server_status)
cli.add_command(get_alerts_count)

if __name__ == "__main__":
    cli()