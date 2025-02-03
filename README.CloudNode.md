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
- Utilities: ElasticSearch

And are considering additional technologies: 
- IAM: keycloak
- Diagnostics: OpenTelemetry/LGTM [[see also]](https://www.youtube.com/watch?v=1X3dV3D5EJg)

This whole process takes about six hours depending on your proficiencies and incongruencies, and we anticipate
releasing and language driven engineer bot to perform this installation and its corrections by the end of 2027,
or received from a member of our starred community. For now, issues should be posted to repository the issues tab.

New opinion unlocked: `Installation Speedruns` should be a subcategory of [deep learning benchmarks](https://github.com/davidbernat/Awesome-Installation-Speedruns). (DB 11:17AM 1/29/25) 

#### By the end of this walkthrough...
The purpose of this walkthrough is to establish an operating Python machine server in a new local area network underneath
a router capable of all the expected utilities within a local network: 
- configured static local IP addresses, 
- openSSH via command line into the new machine, 
- local DNS hosted on the machine so all local end devices can access machine services from browsers or terminals
- email server for sending emails within the network without any outside providers
- gitlab for software code version control repositories
- owncloud for self-hosted cloud storage across the local network
- nginx for a robust single-point-of-entry for web users and cybersecurity
- docker for hosting nearly limitless additional services with nearly no additional configurations
- Python for engineering software nearly ready for deep learning on the GPU
- cloudnode for ease-of-use building of small apps as a cloud docker service

This system is a small replica of a modern infrastructure-as-a-service platform for local apps and deep learning.
Its installation guide takes between three and ten hours, bugs permitted; and its text (~10 pages) can be reduced by half in other editions.
This installation uses only commands that can be scripted and automated, bugs permitted; which is why installation speedruns will be important. 

#### Spritely tutorialists providing overviews worth watching? 
- useful for torrents of datapoint to firehose knowledge;
- useful to stare at when that log file is wrong until a shaman arrives
  - Fireship: [100+ Computer Science Concepts Explained](https://www.youtube.com/watch?v=-uleG_Vecis)
  - Fireship: [100+ Docker Concepts you Need to Know](https://www.youtube.com/watch?v=rIrNIzy6U_g)
  - Fireship: [100+ Linux Things you Need to Know](https://www.youtube.com/watch?v=LKCVKw9CzFo)
  - Fireship: [CPU vs GPU vs TPU vs DPU vs QPU](https://www.youtube.com/watch?v=r5NQecwZs1A)
  - Bill Wurtz: [history of the entire world, i guess](https://www.youtube.com/watch?v=xuCn8ux2gbs)
- even more useful? getting back to that log file and working that code


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
3. Make your life easier by creating these environment variables for use in algorithmic configuration files later. Our
goal here is to reduce configurations to these one variable changes followed by a system reboot to reconfigure its settings.
   - Hostname: name your machine as its local IP hostname; mine is http://jarvis.home so: `export STARLIGHT_HOSTNAME=jarvis.home`
   - Local IP: local IP addresses change unless routers configure them to be constant; `hostname -I` will reveal yours: `export STARLIGHT_LOCAL_IPV4=10.0.0.88`
   - NOTE: this is an experimental incomplete feature; not all configurations use these because we are still updating.
   - Create a ticket if you have further improvements. 
4. You may want to take a moment and configure your new machine to receive a static, non-dynamic local IP address from your router.
This needs to be done by logging into your router via a browser; instructions are online for most ISPs, i.e., mine required logging
in with the default admin username at `http://10.0.0.1/` which opened to "Settings => Connected Devices" then an "Edit" button for
machine `jarvis`. This will ensure your machine always has the same local IP address after every reboot; even though future cloudnode
code can easily access the local IP to store in the environmental variable on each reboot.

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
   - Identifying the local IP address: `ip address`
   - NOTE: https://devconnected.com/how-to-install-and-enable-ssh-server-on-ubuntu-20-04/
2. We are creating the `/home/server/_server/` directory for any applications that require special directories, i.e.,
   ownCloud. We will assume that cloudnode applications (i.e., repository created servers) are put into this directory.
3. We will create a trivial http service using `busybox` on port 8000 to operate as trivial health checks that systems are operating effectively. The `busybox` will server `index.html` contents in its working
  directory. In future servers we will develop the practice of using `/server-<application>/` and `/docker-server-<application>/`
  in the `/home/server/_server/` to encapsulate services independently. We will generally give each application a block of 10 ports,
  sequentially, between 8000 and 9000; later cloudnode will retain a system registry and operate much of these stages algorithmically.
- create `mkdir /home/server/_server/server-trivial/` and `echo "hello, from cloudnode healthcheck." > /home/server/_server/server-trivial/index.html`.
- add one uri to test those too: `mkdir /home/server/_server/server-trivial/example/` and `echo "hello, from inside a uri endpoint at example/page.html" > example/page.html`
- enter that directory and start the service: `busybox httpd -p 8000`
- test that these work: `curl -v http://10.0.0.88:8000` and should not work from an external machine because of the firewall.
- Add a firewall allow: `sudo ufw allow 8000 comment 'temporarily allow 8000 during installation'`
- Add a line in the cron setting to restart upon reboot: `sudo crontab -e` then add `@reboot cd /home/server/_server/server-trivial/ && sudo busybox httpd -p 8000`

### Installation: why does our machine we need our own local DNS server?
1. The short answer is that a local DNS server is lightweight and simple to set up, and each end user device can be instructed
to use our local DNS server when connected to our local router, and fallback to its usual configuration when unavailable,
thereby removing any responsibility for any end users to manage anything concerning network configurations or IP addresses. 
In short: a local DNS server is the correct way to construct a local network for its end users.
2. Okay. Why? Later, our machine hosts various servlets providing system tools, containerized services, or cloudnode applications,
and therefore needs an ingress management system to direct traffic. The machine itself handles this by running each service on its
own port, and shielding the machine by firewalls to allow or deny specific inbound traffic. But all this configuration is
centric to the machine administrator; not the end users who simply want to access `gitLab`, hosted on our `jarvis.home` network.
    - The machine itself can handle its own administration: its own local IP, its assigning of ports to the various services, its firewalls,
decisions to scale an application with multiple containers running on multiple ports, whether a service is actually a white-label mask of a
global network API hosted elsewhere, and so on. This fundamental principle correctly creates two roles, the end user and the machine 
administrator, each responsible for management of simple data they easily access and update. 
    - In short, the end user wants to access`http://gitlab.jarvis.home/`, not its local IP on that one port, except wait, we moved ports when we installed that other application
because its configuration file was broken, or did we move to a cloud-hosting for a few weeks while the patch for that other bug was
being created uh, `http://10.0.0.88:8010/` worked last time let me start there. 
    - In practice, we accomplish much of this by installing `nginx` as an ingress manager so that we can firewall nearly all traffic except
HTTP port 80, and configure `nginx` to make a relay, called a proxy pass or reverse proxy, to any existing machine services using specific 
`localhost` calls, then return the result back through `nginx` to the end user; this is the machine administrator role. The only remaining
question is how to get end user URL traffic specifying "gitlab on jarvis.home please" to the `nginx` ingress itself sitting on the specific machine: this is the
purpose of the DNS service we are installing; and why there are ad-hoc ways to achieve this without a DNS service, they are all fundamentally broken in practice.
3. If you want to know how the alternative approaches are broken then read this item. Otherwise, skip to installing the DNS service.
    - There are two ways URL syntax to configure a single-point-of-entry to a set of machine servlets, i.e., what we will use `nginx` to: 
by subdomain, so that `http://<application>.jarvis.home` inbound to the machine relays to application once inside the machine, or by URI noun, 
so that `http://jarvis.home/__<application>/` does. Both have limitations that ultimately lead to our decision to create a DNS server.
    - Using `http://<application>.jarvis.home` is clean and confirms to broad web standards that subdomains silo applications and that all
URIs associated to a subdomain conform to internal configurations of that subdomain only, operating independently as applications. Unfortunately,
choosing subdomains suffers from several frustrating needs from every new end user unless a DNS service is also built. Chiefly, subdomains cannot be
used with IP addresses, which means that using or testing `http://<application>.10.0.0.88` is invalid, locking each user into hostname resolution
even during debugging, which means every user is de-facto responsible to resolve `<application>.jarvis.home` into `10.0.0.88` in order to use any of machine services,
which is the function of a local DNS service. Each user can approximate this very easily by modifying their own `/etc/hosts` file, as explained elsewhere,
but wildcards cannot be used: each subdomain to IP pairing must be explicitly listed in that file each time a new subdomain is added or IP address changes,
and even were end users capable of doing this fragile management, phones do not have this hosts file, and so might not edge/IoT devices, locking them out.
This method requires, for nearly all intents and purposes, a DNS server for ease of use, persistent management, and unified availability across all devices.
  - Using the `http://jarvis.home/__<application>/` is clean and effective for entering services, implies private silos using the `__` prefix,  and can be used
as `http://10.0.0.88/__<application>/` meaning that every user can access directly via the local IP for testing and debugging, including phones and other devices;
and should the end user want to use `jarvis.home` instead then only that host ever needs to be added to a `/etc/hosts` file as there are no subdomains.
But this approach is crippled by one fatal limitation: when web content returns to the browser and contains in-page URLs written as relative URIs from root `/`, 
i.e., `<a href='/example/page.html'></a>`, there is absolutely no way to inform the browser that the content needs to be sourced 
from `http://jarvis.home/__<application>/example/page.html`, and the browser will carry out its instructions to get the current hostname and access the URL relative
to that, `http://jarvis.home/example.page.html`, which is wrong. The only way to address this is to re-write in-document URLs of the content generated by every 
application of every request, which is infeasible and insanity. It is a no-go.
3. Installing `dnsmasq` on our machine is lightweight and only a few lines of configuration. From there, all that needs to be done is to `ufw` allow its 
port 53, the default for all DNS servers, and configure each device to use our local DNS service. What DNS server to use is a configuration setting 
specific to each device and router: in the same network settings as where you put its password, for instance. 
  - Notes: https://computingpost.medium.com/install-and-configure-dnsmasq-on-ubuntu-22-04-20-04-18-04-1919a438e80d
  - Incorrect: https://help.ubuntu.com/community/Dnsmasq
  - We are using `dnsmasq` to replace the `systemd-resolved` service; disable its restart on reboot: `sudo systemctl disable systemd-resolved & sudo systemctl stop systemd-resolved` 
  - Install: `sudo apt install dnsmasq`
  - Now we edit `sudo nano /etc/dnsmasq.conf`
  - Remove the `#` from `domain-needed` and `bogus-priv` so that these are active, to increase security and ease of use.
  - Remove the `#` from `no-resolv` to get global public DNS server choices only from this configuration file.
  - Add the two upstream DNS `server=8.8.8.8` and `server=4.4.4.4` requirements; these specify global public DNS servers to use
in their order of priority. The `8.8.8.8` and `4.4.4.4` IPs are operated by Google; `208.67.222.123` is operated by OpenDNS; and
you can either log into your router or search your "Settings => Network Settings" on your phone to find the DNS servers your ISP 
uses. We opted to use our ISP DNS IPs, e.g. `75.75.75.75`, and would not ever choose to use Google or Cloudflare. 
  - Directly above your `server=` settings add your local network hostname `address=/jarvis.home/10.0.0.88`
which will now direct all such traffic including subdomains to that local IP address; only when an address match is not
found will the local DNS server reach out to the global DNS servers listed below.
  - Set the `cache-size=1000` which will cache results of the last 1000 DNS lookups for speed, since global DNS lookup 
can take dozens to hundreds of milliseconds. 
  - Now add `listen-address=127.0.0.1, 10.0.0.88` and `port=53` to instruct `dnsmasq` to accept inbound traffic from devices connected to the router.
  - I did not use `expand-hosts`, as we do not want to have the DNS service expand `jarvis` to `jarvis.com` etc., and `strict-order`, as we have only one DNS service.
  - The rest of the instructions are confusing; do not change `/etc/resolv.conf` which is used for instructing your machine
for which DNS servers to use as a browser, i.e., the same changes you will need to make to each of your computers.
  - Add `log-queries` and `log-facility=/var/log/dnsmasq/access.log` which will enable logging; but you must make that directory and 
`touch` that file or else the service will throw an error.
  - Now we edit `/etc/resolv.conf` which lists any DNS servers the machine should search through. 
  - First unlink its current link to a different service: `sudo unlink /etc/resolv.conf`
  - Replace the entire file with one line: `nameserver 127.0.0.1`, which tells the machine to simply send a request to itself 
which will now be received by `dnsmasq` as we configured this before; this helps for certain requests from `localhost`.
  - Now we edit `sudo nano /etc/default/dnsmasq` to remove the `#` from `DNSMASQ_EXCEPT="lo"` and `IGNORE_RESOLVCONF=yes`
  - Start or restart the service `sudo systemctl restart dnsmasq` and use `status` to check that you have no errors.
  - Test using the `dig` operation which returns DNS query results: `dig jarvis.home` and `dig cnn.com` should both return
correct results; with the former resolving to your local IP and the latter referring to the global public IP of `cnn.com`.
  - If so, it works! Now simply update each end user machine. 
  - Add a firewall allow: `sudo ufw allow 53 comment 'Local network DNS service'`
  - Enable the service to start at reboot: `sudo systemctl enable dnsmasq`
  - How to add our local DNS server to any device: on your device go to "Settings => Wi-Fi" (or Ethernet) then the information
about your specific network you use. Among the settings for "Auto-Join" and "Password", etc., will be one for "Configure DNS". There
you will see a list of several DNS IP addresses, which may even look familiar now. Add your machine local IP (mine is `10.0.0.88`) to the top of this list
so that your phone always tries to resolve DNS using your machine before falling back to its former options if your machine is not available.
   - The URL `http://jarvis.home:8000` and `http://10.0.0.88:8000` should both work for you from any of these devices, presuming the `busybox` server is still running.


### Installation: nginx, then reconfigure machine access via proxy
1. We will install `nginx` as a tool service using `apt` instead of docker so that we can more easily create and edit
   configuration files for each of our different services; and because nginx is fundamentally closer to an operating system
   tool than a service application. We are going to configure `nginx` on port 80, to handle all HTTP traffic to internal
   services.
   - Installation: `sudo apt install nginx`
   - Stop any services that might be running on port 80: `ss -tulpn | grep --color :80`
   - configure our simplified http proxy by placing the following configuration into `/etc/nginx/sites-available/trivial.conf`
     and create a symlink to its enabling directory using `sudo ln -s /etc/nginx/sites-available/trivial.conf /etc/nginx/sites-enabled/trivial.conf`.
     When that symlink is not present nginx will ignore the configuration and not create that server forwarding purpose.
   - For our `trivial` server we use the following substitutions: `INTERNAL_PORT=8000`, `SUBDOMAIN=trivial`, `HOST=jarvis.home`,
     `MAINTAINER=<your everyday email>`, `SUBDOMAIN_PORT_CLUSTER=TRIVIAL_8000_CLUSTER`, `INGRESS_PORT=80`, and `INITIATED_TS` as
     an approximately now timestamp in a reasonably machine-parsable way.
   - Test that the configuration has correct syntax and is valid: `sudo nginx -t -c /etc/nginx/nginx.conf`
   ```
   # this configuration file should be saved as /etc/nginx/sites-available/SUBDOMAIN.conf
   # by default we use SUBDOMAIN_PORT_CLUSTER as the cluster name; and assign a weight=1 to imply future load balancing.
   upstream SUBDOMAIN_PORT_CLUSTER {
       server localhost:INTERNAL_PORT/ weight=1;
   }
   server {
       listen INGRESS_PORT;                              # ingress port from external Internet IPv4
       listen [::]:INGRESS_PORT;                         # ingress port from external Internet IPv6
       server_name SUBDOMAIN.localhost SUBDOMAIN.HOST;   # inbound to its application subdomain

       # proxy_pass email=MAINTAINER address ts=INITIATED_TS reason=proxy_pass to maintained service
       # users are recommended to access this server by http://SUBDOMAIN.localhost/
       location / {
           proxy_pass http://SUBDOMAIN_PORT_CLUSTER/;  # forward to internal designated port [for docker]
           
           # For debugging: these lines can replace those above to return request information.
           # add_header Content-Type text/plain;
           # return 200 "this_file=SUBDOMAIN.conf inbound_host=$host this_server_name=$server_name document_root=$document_root, request_uri=$request_uri";
       }
   }
   ```
   - reload the configuration `sudo nginx -s reload` and start the service `sudo systemctl restart gitlab-runsvdir.service` and navigate to `http://trivial.jarvis.home/` from an external browser.
   - log files: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
   - The URLs `http://trivial.jarvis.home` should now work across your local network, entering through port 80 and allowing `nginx` to relay internally to port 8000; assuming the `busybox` service is running.
   - Close the firewall: `sudo ufw remove allow 8000`


### Installation: Postfix to prepare for gitLab as tools, later ownCloud and docker servers
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

### Installation: gitLab, and configuring programmers on your local IP network
1. Installing `gitLab` using the `apt` package manager as a tool rather than a containerized service as an application moves
the system of code management closer to the metal of the operating system, which is more natural, and also relatively easy to install.
We will install this with HTTP on port 8010 and configure `nginx` to redirect from `http://gitlab.jarvis.home/` to that port. 
   - Installation of Enterprise Edition is relatively straightforward, though there are bugs in bad documentation.
   - First, add the keyring for `apt` by preparing these steps in the manual install: https://packages.gitlab.com/gitlab/gitlab-ee/install#manual-deb
   - Second, select a root user password, which must be eight characters or else the installation may silently error.
   - Third, install Enterprise Edition for the URL: `sudo GITLAB_ROOT_PASSWORD="<password>" EXTERNAL_URL="http://localhost:8010" apt install gitlab-ee`
   - Confirm the service is running `sudo gitlab-ctl status` and navigate to a browser to login with its admin user `root`.
   - BUG: we found that the `/install#bash` scripts for the first step failed to correctly add the keyring for `apt`.  
   - BUG: the installation may throw a `permission denied` on the keyring `.gpg` file. In this instance I found I needed to change
the permissions to `chmod 777`; which simply provides all users the opportunity to install via `apt`, harboring no security risk.
   - BUG: If you receive an error that `EXTERNAL_URL` must be `https://` then simply set the URL as such and change back to HTTP in the configuration
file `/etc/gitlab/gitlab.rb` after successful installation.
   - BUG: installation requires SSL configuration and I found that on occasion the LetsEncrypt/ACME SSL failed to establish a connection during installation, in part because the `github.rb` configuration
defaults did not match the documentation. In this case, you need to manually add these two lines into its `letsencrypt` section. 
This information is a composite of information here: https://docs.gitlab.com/omnibus/settings/ssl/#use-an-acme-server-other-than-lets-encrypt 
then after any update to the configuration file you must reprocess using `sudo gitlab-ctl reconfigure`.
   ```
   letsencrypt['acme_staging_endpoint'] = 'https://acme-staging-v02.api.letsencrypt.org/directory'
   letsencrypt['acme_production_endpoint'] = 'https://acme-v02.api.letsencrypt.org/directory'
   ```
2. Login from a browser as `root` to establish root account and update specific settings, and use as you normally would
GitHub. Remember that because this machine is not connected to an outbound DNS service on the global, public Internet, that
all user email addresses and URLs must be local network, c.f. `user@jarvis.home`. There are other actions the administrator
account should take in the "Admin Area => Settings" area to create a security protection should your machine ever become
accessible to the global public Internet: 
      - In "Sign-up restrictions", remove the check on "Sign-up enabled" then whitelist your email address domain (e.g. `jarvis.home`).
This will require the administrator account to create all new users through either the dashboard or its API.
3. Use the admin to create new users for your local network and cloudnode users, but not server and postmaster (i.e., any programmers).
   - Once the administrator creates your account you will receive an email in your `jarvis.home` account; and in the text body
of that email is a URL inside an HTML tag that contains its confirmation link with its password token. Copy and paste that into
the browser so that you are asked to provide your password; then login to the dashboard. 
   - Familiarize yourself with the diverse platform of tools in gitLab: it rivals and exceeds GitHub, and GitHub started as a direct
clone of gitLab much as you have here.
   - Create a gitLab token for `git` for the command line in "User settings => Access Tokens".
   - Further Administrator-level API endpoints allow total operation of the dashboard from the command line. 
   - NOTE: https://docs.gitlab.com/omnibus/settings/dns
   - NOTE: https://docs.gitlab.com/ee/api/rest/
   - NOTE: https://docs.gitlab.com/ee/api/users.html
   - NOTE: https://docs.gitlab.com/ee/api/users.html#user-creation  # create new users
   - NOTE: https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html
4. Configure `nginx` to redirect `http://gitlab.jarvis.home` to port 8010 by creating and linking additional nginx conf `gitlab.conf` using the same methods
as we did for `trivial` and using these new variable values: `INTERNAL_PORT=8010`, `SUBDOMAIN=gitlab`, `SUBDOMAIN_PORT_CLUSTER=GITLAB_8010_CLUSTER`. All of the
URLs and APIs should immediately work on each of the DNS configured devices using `http://gitlab.jarvis.home` after correctly rebooting the `nginx` service.
   - Notice we installed `gitlab` on `http://localhost:PORT` without any particular reference to other machines or the router.
   - These reduce the security interfaces effectively entirely to the `nginx` ingress point. 
   - If you opened `ufw allow 8010` to test remember to remove its rule. 

### Installation: docker services, then ownCloud
1. Installation of docker is a series of simple commands. The docker management system is automatically configured to
   launch in the background at start and reboots; whether a specific container restarts 'on reboot' is established by
   restart polices created for that specific container.
   - Install using the `apt` method in `https://docs.docker.com/engine/install/ubuntu/`. Its steps about keyring instructs `apt`
     how to install docker directly from the `apt` command itself; which is done once and will allow updates to be scheduled as part
     of the other `apt` updates the server implements.
   - NOTE: https://docs.docker.com/config/containers/start-containers-automatically/
   - NOTE: https://docs.docker.com/engine/security/#docker-daemon-attack-surface
2. This has created a new machine user group `docker` with zero members; and all service administrators of docker must be
   members of this group. Cloudnode is intended to operate the deployment of services through dockerized containers throughout
   the process of app development, and to use the `server` username; so this user must be added.
   - Add `server` to `docker` and enter into that group: `sudo usermod -aG docker server & newgrp docker`
   - We recommend only adding the superusers of the machine to the usergroup; and those tools which explicitly require this.
   - NOTE: https://stackoverflow.com/a/48957722
3. Install `docker-compose` for our orchestration uses.
   - Installation: `sudo apt install docker-compose`
   - Our convention will be that docker and compose files are stored in `/home/server/_server/<application>-docker-server/` and designed
     for `nginx` to be algorithmically configured to redirect to its application port using `http://<application>.jarvis.home/`. When
     additional subdomains are necessary use sub-subdomains. Each service will receive a block of ten ports sequentially up from 8020, 
     with `trivial` at 8000 and `gitlab` at 8010; these information will be stored in a text file registry later using cloudnode.

### Installation: ownCloud, and redirect using nginx
1. ownCloud boasts self-hosted on-prem the same functionality as real-time Google/DropBox with stated increases in security,
  although that claim is not verified by us, and is used by CERN and several Swiss firms, including financial and crypto
  firms; about as best as our machine can get in the open source and free ecosystems. this allows us to store files from
  any computer in our network as we would Google Drive and provides both a similar interactive browser interface as Google
  Drive and an API in Python for our written programs to use its functionality. its shareable links will only be accessible
  inside our local network (unless we open our router to accept global public Internet inbound); however, be mindful that
  our machine is currently only a cloud of one machine: our files are not distributed over dozens or hundreds of redundancy
  backups across multiple computers in various geographic locations; we have one hard drive, same as any external hard drive.
  we will address these limitations in future updates, including selecting an inexpensive cloud provider to automatically
  redundancy backup our local files here in an unreadable form to our cloud provider. it is a very good system considering
  these limitations.
   - Create `sudo nano /home/server/_server/owncloud-docker-server/docker-compose.yml` and copy the ownCloud docker compose file into it.
   - NOTE: https://doc.owncloud.com/server/next/admin_manual/installation/docker/#docker-compose
   - ownCloud uses three services: storage on disk, mariadb; storage in memory, redis; interface and apis, owncloud.
   - Data persistence across reboots: 
   - Create `owncloud-docker-server/.env` and notice our change to port 8020 and its latest version. 
``` 
OWNCLOUD_VERSION=latest
OWNCLOUD_DOMAIN=localhost:8020
OWNCLOUD_TRUSTED_DOMAINS=localhost
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<password>
HTTP_PORT=8020
```
2. Launch `sudo docker compose up -d`
3. Configure `nginx` to redirect `http://owncloud.jarvis.home` to port 8020 by creating and linking additional nginx conf `owncloud.conf` using 
`INTERNAL_PORT=8020`, `SUBDOMAIN=owncloud`, `SUBDOMAIN_PORT_CLUSTER=OWNCLOUD_8020_CLUSTER`. It should be immediately accessible after restarting `nginx`.
   - BUG: owncloud via Docker currently has a problem ingesting `.env` variables for `OWNCLOUD_TRUSTED_DOMAINS` that restrict access to its login screen
from outside the localhost of the machine. We are working on this; and this should be resolvable through `.env` variables itself, never entering the
running service and editing the `config/config.php` configuration file despite the prevalence of search results prompting system administrators to do so.


### Installation: Python, plus CONDA, and a handful of other packages.
1. Python is the primary software engine of data science and deep learning, robust for full backends and enough frontends, 
easy to learn. Python downloads packages which are imported into their software code; different projects require different
packages, and so "environment" managers exist, primarily pyenv and CONDA, which allow you as developer to silo different
projects when you need to be certain your projects have not used packages installed from other projects. CONDA is what
we will primarily use because many deep learning packages are especially geared toward CONDA.
2. pyenv. note that installation is quick but requires an appending to ~/.bashrc
   - install: https://gist.github.com/trongnghia203/9cc8157acb1a9faad2de95c3175aa875
   - we needed additional packages: `sudo apt install liblzma-dev libffi-dev`
   - we used this to install the latest version of non-dev Python, 3.13.1 as of 20250202.
   - if your system is missing libraries and errors are thrown simply `apt` install those libraries
3. Conda installs in ~/miniconda so both pyenv and CONDA are part of username server.
   - install using the Linux terminal steps: https://docs.conda.io/projects/miniconda/en/latest/
   - Create and activate a new default environment named SERVER: `conda create --name SERVER && conda activate SERVER`
   - Turn off the default activation of an environment named `base`: `conda config --set auto_activate_base false`
   - Add this to `~/.bashrc` to activate into `SERVER` by default: `echo "conda activate SERVER" >> ~/.bashrc`
   - Install the `pip` package installer for Python which is what we will use by default: `conda install pip`
   - For the most part we are finished with our default installation except for cloudnode itself. 
4. In the next few days we will tighten this document and add several introductory deep learning benchmarks.


### Where are the other components?

We are in the process of porting over from other repositories.

## Hire us to build.

![ferris.bueller.png](cloudnode%2F_db%2Fdocs%2Fferris.bueller.png)

<br /><br /><br />
Starlight LLC <br />
Copyright 2025 <br />
Not licensed for commercial use <br />
