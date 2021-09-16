# PollenisatorCLI
Command Line Interface client for pollenisator

### Installation:

```
git clone https://github.com/fbarre96/PollenisatorCLI
cd PollenisatorCLI
pip install .
```

### Usage

Run it as CLI
```pollenisatorcli [--host XXX.XXX.XXX.XXX --port 5000 --http]```

OR

Run it in shell
```pollenisatorcli ls ips```

### Login
![Login](./docs/screens/login.png)

### Create a pentest
![new_pentest_wizard](./docs/screens/new_pentest_wizard.png)

### Forms
For every forms you can use show/set/unset or use the wizard

![Show](./docs/screens/show_form.png)

### Open a Pentest
Autocompletion with TAB is available on most commands / parameters.

```
Pollenisator > ls
Pentests:
==========
demo
AlgoSecure-Training
algo-test
test-algo
```
![Example](./docs/screens/open_with_autocomplete.png)

### List hosts of a pentest
![Example](./docs/screens/ls_ips.png)

### List all tools executed on an ip
![Example](./docs/screens/tools_in_ip.png)

### Insert an new object in database
![Example](./docs/screens/insert_ips.png)

### Interact with objects
![Example](./docs/screens/edit_ip.png)

### Import existing tools results
Pollenisator server has plugins that auto-detects which tool generated it and extract informations.

![Example](./docs/screens/import_file.png)

### Execute commands to import automatically
Pollenisator server has plugins that auto-detects which tool you are trying to execute it and modify it with its expected output argument so you don't have to worry about which format is exepected.

![Example](./docs/screens/exec_result.png)

### Execute any command from anywhere and import them

#### Pollex
  Pollex allows you to execute and import commands from any terminal if you are connected.
  
  ```$ pollex nmap -p80,443 10.0.0.0/24```
#### Terminal
  You can also spawn a terminal configured to trap every command and send them to pollenisator using
  
  ```Pollenisator demo > terminal trap_all```
![Example](./docs/screens/terminals.png)

### Manage workers
#### Boot a new worker from docker
![Example](./docs/screens/boot_worker.png)
#### List workers and allow them on your pentest
![Example](./docs/screens/list_workers_and_inclusion.png)
#### Execute a tool using a worker
![Example](./docs/screens/launch_with_worker.png)

### Auto scan 
If workers are configured, you can perform an auto-scan that will execute programed commands
![Example](./docs/screens/autoscan.png)

### Dashboard
![Example](./docs/screens/dashboards.png)

### Reporting module
![Example](./docs/screens/report.png)

Then you can generate a powerpoint or word document
![Example](./docs/screens/report_generate.png)

### Script manager
Write custom scripts to interact with the API

![Example](./docs/screens/scripts_manager.png)
