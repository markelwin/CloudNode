### Welcome to your purchase of a new CloudNode self-contained on-prem enablement system.
#### Starlight LLC

This step-by-step guide will aid novice engineers and engineer bots in the software installation steps
required for transforming on-prem hardware systems into local and global area network computer systems 
ready to operate cloudnode server systems for calculations or apis. The system uses open source on-prem
alternatives wherever possible and results in inexpensive hardware scalable for engineer bots to inject
their generated service calls within a managed system administration architecture of resources. We take
the approach that deep learning is computational compute and generative networks are operating systems
localized on-prem within the domicile with user agents issued externally to provide external value or work.

We use the following technologies: 
- Base: Ubuntu
- Network: OpenSSH, Docker, nginx
- Storage: ownCloud
- Repositories: gitLab
- IAM: keycloak
- Utilities: ElasticSearch

This whole process takes about six hours depending on your proficiencies and incongruencies, and we anticipate
releasing and language driven engineer bot to perform this installation and its corrections by the end of 2027,
or received from a member of our starred community. For now, issues should be posted to repository the issues tab.

### Installation: Ubuntu via USB
1. Installing the Ubuntu OS via USB stick has nothing out of the ordinary, except for a few configurations, and we are
   specifying several conditions here for utility of the platform at large: we used Ubuntu 24.04.3 LTS (the most up-
   to cn_date version with Long Term Support so that stability can be presumed) and installed the minimum configuration
   version (browser, few tools; nothing else); and no password for reboot (i.e., so power cycling can be automated).
   We used Etcher to transform the ISO disk image into a USB bootable image.
   - NOTE: https://ubuntu.com/tutorials/create-a-usb-stick-on-macos
   - NOTE: https://etcher.balena.io/
2. Creation of server user (name=SERVER, granted sudo/root privileges).
   The server user will operate all system administration on behalf of the cloudnode, and we may use `server` 
   interchangeable below as the de facto user. 
   ```
   sudo adduser server           # enter name SERVER when prompted.
   sudo usermod -aG sudo server  # adds user to sudo/root
   su - server                   # fully switch into the server user 
   ```
   - NOTE: we presume all installation commands below are by the SERVER user instead of root

### Installation: OpenSSH configurations, firewalls, and initial configurations of users
1. First thing to do is to establish an OpenSSH server operating on an unknown port to allow remote access to the
   machine as a server. All subsequent installations will be performed from a command line so that these can be
   scripted. We will use port 6137 for SSH, rather than the default 22, and need to construct firewall rules to allow 
   inbound communication the `ufw` package. We will leave unrestricted outbound communications, and we will not whitelist our
   inbound IP addresses: i.e., we will allow any IP address to SSH into the machine at this initial configuration
   stage. We will add firewall rules to allow HTTP/S, i.e., to configure the machine to allow inbound HTTP/S requests
   at their default ports (80 and 443 respectively) to allow our servers to operate on HTTP/S. Updating ufw does not 
   require a service reboot; updating OpenSSH does. Generally speaking these online resources are straightforward and 
   simple. We will be using passwords and not SSH Keys to login at this time.
   - The installation of the OpenSSH server: `sudo apt install openssh-server`
   - The status of the OpenSSH server can be accessed with this: `sudo systemctl status ssh`
   - The default SSH configurations: 
   ```
    sudo ufw enable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow http
    sudo ufw allow https
    ```
   - The addition of the ufw rule for SSH; notice the comment: `sudo ufw allow 6137 comment "Using 6137 for SSH Inbound"`
   - The status of the ufw rules: `sudo ufw status`
   - Identifying the LAN IP address: `ip address`
   - NOTE: https://devconnected.com/how-to-install-and-enable-ssh-server-on-ubuntu-20-04/
2. We are creating the `/home/server/_server/` directory for any applications that require special directories, i.e.,
   ownCloud. We will assume that cloudnode applications (i.e., repository created servers) are put into this directory.


### Where are the other components?

We are in the process of porting over from other repositories.

## Hire us to build.

![ferris.bueller.png](cloudnode%2F_db%2Fdocs%2Fferris.bueller.png)

<br /><br /><br />
Starlight LLC <br />
Copyright 2025 <br />
Not licensed for commercial use <br />
