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
- Network: OpenSSH, Docker, Postfix, nginx
- Storage: ownCloud
- Repositories: gitLab
- IAM: keycloak
- Utilities: ElasticSearch

This whole process takes about six hours depending on your proficiencies and incongruencies, and we anticipate
releasing and language driven engineer bot to perform this installation and its corrections by the end of 2027,
or received from a member of our starred community. For now, issues should be posted to repository the issues tab.

New opinion unlocked: `Installation Speedruns` should be a subcategory of deep learning benchmarks (DB 11:17AM 1/29/25) 

#### Spritely tutorialists providing overviews worth watching? 
- useful for torrents of datapoint to firehose knowledge;
- useful to stare at when that log file is wrong until a shaman arrives
  - Fireship: [100+ Computer Science Concepts Explained](https://www.youtube.com/watch?v=-uleG_Vecis)
  - Fireship: [100+ Docker Concepts you Need to Know](https://www.youtube.com/watch?v=rIrNIzy6U_g)
  - Fireship: [100+ Linux Things you Need to Know](https://www.youtube.com/watch?v=LKCVKw9CzFo)
  - Fireship: [CPU vs GPU vs TPU vs DPU vs QPU](https://www.youtube.com/watch?v=r5NQecwZs1A)
  - Bill Wurtz: [history of the entire world, i guess](https://www.youtube.com/watch?v=xuCn8ux2gbs)

### Installation: Ubuntu via USB
1. Installing the Ubuntu OS via USB stick has nothing out of the ordinary, except for a few configurations, and we are
   specifying several conditions here for utility of the platform at large: we used Ubuntu 24.10 (the most up-to-date
   non-LTS version so that we can contribute to the Ubuntu ecosystem) and installed the minimum configuration
   version (browser, few tools; nothing else); and no password for reboot (i.e., so power cycling can be automated).
   We used Etcher to transform the ISO disk image into a USB bootable image.
   - NOTE: https://ubuntu.com/tutorials/create-a-usb-stick-on-macos
   - NOTE: https://etcher.balena.io/
   - NOTE: we will refer to our machine as `jarvis` and its local IP host location as `jarvis.home`
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
   scripted. Previous versions of Ubuntu used to allow non-default ports for SSH simply; but no longer, so we will use
   default 22, and still need to construct firewall rules to allow 
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
    sudo ufw allow ssh
    ```
   - How to add arbitrary ufw rules; notice the comment: `sudo ufw allow PORT comment "Using PORT for Example Inbound"`
   - The status of the ufw rules: `sudo ufw status`
   - Identifying the LAN IP address: `ip address`
   - NOTE: https://devconnected.com/how-to-install-and-enable-ssh-server-on-ubuntu-20-04/
2. We are creating the `/home/server/_server/` directory for any applications that require special directories, i.e.,
   ownCloud. We will assume that cloudnode applications (i.e., repository created servers) are put into this directory.

### Installation: Postfix to prepare for gitLab; later nginx for ownCloud and docker servers
1. gitLab requires Postfix, the open source email transfer server, and so we might as well establish an email service
on our local area network, which we can always redirect to the global public DNS services in the future to operate our
email services same as the public alternatives. Installing Postfix has a slightly higher technical bar than the other
steps in this process but remains more or less straightforward. Postfix is an SMTP server that allows mail creation, 
send, and receive within a local area network, which also makes the server email addresses of each machine and cloudnode
user a convenient way to pass messages, reports, and status updates during service processes. To send email outside the
local area network and into the global public Internet requires either an additional SMTP forwarding service, i.e., 
Gmail provides one similar to the way Gmail can be used inside Python to send emails, or to have access to a FQDN 
(fully qualified domain name), i.e., a domain hostname that is registered within the DNS lookup services of the
broader web, and access to its M and DX settings. In other words, sending email to the broader Internet requires 
pointing the SMTP service to a DNS lookup service, that then reaches the domain hostname and its DNS settings (i.e., Wix
or EuroDNS), which instructs the email on how to deliver itself. The Postfix server also expects its own special user
on the machine to operate as postmaster, and which also receives administrative errors to its postmaster email inbox.
We will create this user as postmaster, and walk through a description of the configuration, which I found confusing. 
The postmaster will have sudo privileges. Do not switch into user postmaster; we will conduct all steps as user server.
   ```
   sudo adduser postmaster
   sudo usermod -aG sudo postmaster
   ```
2. We will use `apt` to install Postfix by installing the relatively low-level mail utilities client `mailutils`, which
provides us infrastructure and clients for mailboxes and other basic facilities of email on top of the transport structure
of Postfix. The installation process requires several interactive setup answers which are somewhat ambiguous: choose 
`Internet Site` because we are operating an email exchange using SMTP; and for our system the System Mail Name is
`jarvis.home` rather than the machine name `jarvis` because we want to establish a top-level domain hierarchy in our 
network; then we will need to edit the configuration settings directly in its configuration files to confirm.
   - Install mailutils as user server:  `sudo apt install mailutils`
   - The postfix service must be restarted with every configuration change: `sudo postfix reload & sudo systemctl restart postfix`.
   - NOTE: https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-22-04
3. Editing the postfix configuration is best done using `sudo postconf` to access or edit the various settings. We will 
be using a local area network with one machine named `jarvis` to deliver email only within that one machine for now. That
simply means external users will need to log into this machine through browsers, APIs, or directly to access their email.
   - Is the postfix service running: `sudo systemctl status postfix`
   - To access a value, i.e., myhostname: `sudo postconf myhostname`
   - To edit a value: `sudo postconf -e 'myhostname = jarvis'`
Some of the `postconf` variables are slightly confusing so here is a short description, and how each value may need to be changed.
   - `myhostname = jarvis` the variable `$myhostname` refers to the name the machine uses to refer to itself, i.e., the
value returned from the command `hostname -f`, not the domain name of the email addresses `postmaster@jarvis.home` which
can be assigned any domain name or fully qualified domain hostname (FQDN) i.e., `starlight.ai`, which refers to the location
the SMTP server expects to transact as; also, by not having `myhostname = localhost` we do not allow this software to imply `jarvis` 
by using `localhost` instead.
   - `mydomain = jarvis.home` if using an email address domain e.g., `jarvis.home` that is not identical to the machine name e.g. `jarvis`
then this field needs to be set to the email address domain; otherwise using its default `$myhostname` is most appropriate. Remember how
Postfix operates: the SMTP operates on email address string values, which can take any values, to identify what destination machines to
reach, through a network where nodes are provisioned specific IP pathways to relay outside the machine if the machine itself is not the
destination; as such mydomain can be configured to be any email address domain you want; once a destination machine is reached, the
virtualization layer, see item steps below, maps any email address to a specific machine username to write the email message to the file system.
What matters is that any domain you want to create can locate its destination; this changes when using the global public SMTP Internet only in
that this relay and resolution layer is performed by the DNS company responsible for hosting these layers on the global public Internet, and
in retrospect, that domain name needs to be available in order to send mail outward to the global public Internet on those systems. If you 
never intend to send email outside your local network then these systems here are the only ones that matter and you can create any domain name. 
   - `myorigin = $mydomain` because emails are being sent only from this one domain name; postconf settings are expansive
enough to allow this machine SMTP server to send mail on behalf of multiple FQDNs, i.e., `starlight.ai` and `aether.com`, and even to 
be managed by different configuration files on different machines, running different postfix SMTP servers, such that only
certain machines can receive or relay messages on behalf of certain domain names; this also allows an open architecture
core incentive in the global public SMTP Internet, since users can contribute their machines to transact email on behalf of 
others, yet retain the rights of whom to participate on behalf with, i.e., a social network of your home engineer friends,
or to transact your internal messages, but also starlight.ai. notice that we do not include the localhost variants of the
domain name, thereby removing the option of users using localhost as shorthand `jarvis.home`, but also removing the capacity
for the machine to send mail within its machine only, i.e., how gitLab may wish to deliver process messages to its administrator.
we do this so that all messages are implied to be available on all machines on the network. 
   - `mydestination = $mydomain` follows the same expectations as `myorigin`.
   - `mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128` specifies the network search space of IPs and FQDNs to 
search to find available machines which expect to receive message or are available to relay on behalf of the sender. This
value set here is configured to use the local machine only, and to account for the possibility that its self IP address 
may be reassigned, i.e., from 127.0.0.1 to 127.0.0.8. it does not require contact to the router; but our choice to not
include `localhost` in the `$mydestination` field means we do not allow users to send mail by naming the hostname `localhost`. 
   - `notify_classes = resource, software` simply sets which priority levels of errors and problems are sent to `postmaster@jarvis.home`
   - 
   - NOTE: http://www.postfix.org/STANDARD_CONFIGURATION_README.html#fantasy
   - NOTE: http://www.postfix.org/BASIC_CONFIGURATION_README.html#notify
   - NOTE: https://www.postfix.org/VIRTUAL_README.html
4. We do not need to configure firewall allow rules for Postfix because we have configured `mynetworks` to use localhost transfer
networks instead of their local IPs to and from the router; and we do want to specifically block the SMTP default port 25 to prevent
any contingencies were our machine overtaken by malicious algorithms. we will also show how we would configure allow firewalls were we
would configure Postfix to operate machine to machine. 
   - Explicitly deny outgoing port 25 traffic: `sudo ufw deny 25 comment 'Explicit block outgoing SMTP traffics.'`
   - To open SMTP traffics, delete that previous deny rule, then also create this: `sudo ufw allow Postfix`
   - NOTE: more information on firewall security concerns for Postfix: https://serverfault.com/a/1040539
5. So now Postfix has configured its SMTP server to operate its mail transfer agent to send and receive emails for the `jarvis.home` domain
and understands when those messages reach their destination machines, in this case only the `jarvis` machine. Now we need tell
Postfix what to do with those messages once they reach the machine and its file system, and configure mailutils to know how to 
access those file system messages when machine users open mailutils. 
   - `sudo postconf -e 'home_mailbox = Maildir/'` configures Postfix so that each mail message is its own unique file.
   - `sudo postconf -e 'virtual_maps = hash:/etc/postfix/virtual'` sets the file system location of what email addresses map 
to what machine usernames; usually machine username `username` maps to the email address `username@jarvis.home` but this is not 
strictly necessary, and must be strictly specified. This model also allows the same mailutils user inbox to gather the
messages of multiple email addresses; such as the case where all admins of `server` might want to also see the messages 
sent to the `postmaster` i.e., without logging into `postmaster` or forwarding any of the email. These settings specify 
which mailutils users have access to which email addresses. Also note that some tutorials virtual_alias_maps but the 
configuration variable virtual_maps should be used.
   - Inside the `/etc/postfix/virtual` file we add a space-separated list of `<emailaddress> <username_or_emailaddress>`, so 
add these first two users with or without the comments: 
   ```
   postmaster@jarvis.home postmaster  # i.e., deliver postmaster@jarvis.home messages to the filesystem of machine user postmaster
   server@jarvis.home server          # same for the user named server created to handle future server/docker operations
   # myrademailaddress@jarvis.home myusername            # hypothetical creation of an email address not exactly matching your machine username
   # postmaster@jarvis.home myemailaddress@starlight.ai  # hypothetical forward possible if our system sent 'using global public SMTP Internet'
   # @jarvis.home myusername                             # an implementation of a catch-all address for all email addresses not subject to above
   ```
   - Postfix servers must be restarted with every virtual aliases update: `sudo postmap /etc/postfix/virtual & sudo postfix reload & sudo systemctl restart postfix`
6. Nearly completed. We have configured the Postfix server to use local SMTP Internet to transfer and deliver mail to each 
`@jarvis.home` machine, and to subsequently put those mail messages into the users filesystems in the `~/Maildir` directory, as specified
by the `home_mailbox` variable; and, in an odd quirk we need to create its cur, new, and tmp mailboxes inside the Maildir manually or else
the mail messages may not properly configure the local filesystem and subsequent messages may bounce and never be delivered. There are
demonstrations online that suggest doing all this by sending a first email; however I found that problematic with modes that fail
quietly, which are the most frustrating bugs to identify. I found that if the first email fails, for whatever reason, or an email is created
without the incorrect syntax, the directories will not be created. (In my case, a mail syntax created a Maildir file instead of a directory.) The 
difficulty is that when Maildir and its subdirectories are not created correctly, or do not exist, the sending of mail (i.e., testing with 'mail' 
or 's-nail') will fail silently, even in verbose mode: a `dead.letter` file will be created in some instances but the
execution of the command will not reveal this or any other errors. In other words, skipping this step leads to mail to
fail silently and its subsequent debugging has very little to go on, especially for novice engineers, or installation speed runners; and
since this step requires switching to each machine username you may want to consider doing the step after this one as well at the same time.
   - Create the necessary subdirectories for each user, i.e., postmaster, by the user, not sudo: `mkdir -p /home/$USER/Maildir/{cur,tmp,new}`
   - Lastly, set the machine terminal profile to recognize our Maildir when any user opens mail clients in the terminal: `echo 'export MAIL=~/Maildir' | sudo tee -a /etc/bash.bashrc | sudo tee -a /etc/profile.d/mail.sh`
   - NOTE: https://www.postfix.org/virtual.5.html
7. Now we install a mail client to read email and test sending various emails. For this we will use `s-nail`, because we 
found the verbose mode to be more informative, and easier to search for in search engines; ironically, `mail`, which is the
mail client bundled in `mailutils`, is extraordinarily hard to search for because of its simplicity of execution and success.
The application needs to be installed for each machine user; the configuration for the application is machine level, i.e., `/etc/`, 
and so only needs to be done once.
   - Switch into each user using `su - <username>` to install `sudo apt install s-nail` and create an empty `.mailrc` file using `touch ~/.mailrc`
   - Configure the application following four lines are set in `sudo nano /etc/s-nail.rc` or append them to its end:  
   ```
   # added email=<EMAIL> address ts=<TIMESTAMP> reason=initial installation process
   # do /not/ add the inline comments; which will cause s-nail to complain with a warning
   set emptystart        # this allows the s-nail client to function even when the mailboxes are empty folders.
   set folder=Maildir    # this tells the s-nail client that mail is in ~/Maildir
   set record=+sent      # this tells the s-nail client to create a log of sent messages in a ~/Maildir/sent file.
   set v15-compat=yes    # this makes forward compatible the configuration for the eventual update to v15
   ```
   - Send the first email! From machine user server to machine user postmaster: `echo "Sir, there are still terabytes of calculations required before an actual flight is..." | s-nail -v -v -s "I would like to open a new project file..." postmaster@jarvis.home`
   - use `-b` for bcc; `-c` for cc; separate emails by commas; syntax is same for mail except `-v` is equivalent to `--config-verbose`
   - NOTE: https://www.youtube.com/watch?v=Qv_hQrfTyBA
   - NOTE: log files for debugging are `sudo cat /var/log/mail.err` and `sudo cat /var/log/mail.log`
   - Each user can access their email using the `s-nail` command to open a bare-bones text-based client; but recognize that this 
bare-bone local internet structures is the system which even the most powerful graphical interfaces directly interact with, and
we could go a step further to install those, but for the purpose of this section we simply intended created a message passing service for our
local, or global, Internet network; and remember, we configured our system so each email message is a simple individual file in the
`~/Maildir` directory, meaning you can delete those, or copy and transfer those, just like any other data with a small directory wrapping.
8. This installation can be so troublesome and persnickety with assumptions and defaults that I am listing a set of potential 
gotchas here in no particular order. In most cases for some reason even the most basic installs seem to jumble around the basic
configuration at the network or machine level, and most of the information out on the web is bad or outdated, so you might just
have gotten unlucky.
   - this will recompile the virtual addresses, reload everything, and restart the server: `sudo postmap /etc/postfix/virtual & sudo postfix reload & sudo systemctl restart postfix`
   - the machine itself contains aliases from one username to another in `/etc/aliases` and Postfix will use aliases to deliver
to a different username home directory; in my case somehow `postmaster: root` ended up in here and so mapped all mail
to `postmaster@jarvis.home` to `root@jarvis.home` with only a passing mention in `mail.log` and skipping the postmaster mailbox.
After the alias is removed its Postfix hashed database needs to be rebuilt using `sudo newaliases` and then the postfix server restarted.
   - there is no need to transition `virtual_alias_domains = $virtual_alias_maps` from its default value even when you are using a domain
name which is not equal to the machine name, despite what several forums say; and even the official documentation has a small bug in the
description of how to write virtual aliases. This is because by `virtual_alias_maps = $virtual_maps` at its default value, and
`virtual_maps = hash:/etc/postfix/virtual`, all and any aliasing of the domain name is contained already directly in this file, 
i.e., `postmaster@jarvis.home postmaster`. All the writing here makes this sound more complicated than the system is: all that 
happens is the local SMTP relayed any `jarvis.home` mail through its network until a machine with has that as its destination is
reached; then the `/etc/postfix/virtual` file is searched to find a map from the complete email address to a machine username to 
write the message to the appropriate user `~/Maildir`. It is fundamentally that simple no matter how many machines in your network.



### Where are the other components?

We are in the process of porting over from other repositories.

## Hire us to build.

![ferris.bueller.png](cloudnode%2F_db%2Fdocs%2Fferris.bueller.png)

<br /><br /><br />
Starlight LLC <br />
Copyright 2025 <br />
Not licensed for commercial use <br />
