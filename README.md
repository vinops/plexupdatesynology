# What is the script for :question: :label:
This script updated automatically Plex server on Synology NAS when new realease of package is available, regardless of the version of your Synology NAS. Curently when you install Plex package :package: in your NAS Synology you can only updated Plex manually when new version is available, but is so an inconvenient !! :persevere:

# Who using this script :question: :hammer_and_wrench:
- Make sure you have minimum version of `Python 3.8 or 3.9` install in your NAS
- make sure you have installed Git on your NAS before
- Connect to your NAS via SSH ```ssh your_name@your_nas``` (make sure you have activated SSH connection in **Control Panel > Terminal & SNMP** and verify that the **"Enable SSH service"** checkbox is checked)
- `git clone` the repository into the directory of your choice
On your NAS, navigate to the **SynoPlexUpdater** project and execute the **set_env.sh** script. This script creates a virtual Python environment and install the necessary dependencies.
    ```bash
        root@YOUR_NAS:/# sh set_env.sh
    ```
- Create schedule task on your NAS, Go to **Control Panel > Task Scheduler**, click **Create** and select **Scheduled Task**. 
    In the text box **Execute the command**, adapt **you_path** according to where the script will be launched.
    ```bash
        source /you_path/SynoPlexUpdater/venv/bin/activate &&
        python /you_path/SynoPlexUpdater/plex_updater.py
    ```
    and schedule time **for example you can shedule task at 7:00AM all the days**


# Questions :question: :space_invader:
If you have a questions or problems to configure your environment don't hesitate to contact me :speech_balloon:
