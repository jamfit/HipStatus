# HipStatus #

> **This project no longer functions in its current state. Microsoft no longer allows HTTP Basic authentication to the Office 365 REST API.** -- Bryson Tyrrell, Feb 28, 2017

## What were we trying to solve? ##

JAMF Software once used Microsoft Lync for internal chat before moving to HipChat. While everyone enjoys using HipChat much more than Lync, there was a widely used feature that HipChat did not support: presence. If a user was in a meeting in their calendar, Lync would display them as "busy" and then reset the user to "available" once the meeting was over.

We also sought to address another issue involving an employee's timezone. When a user account is created from Okta (we use Okta for managing our HipChat accounts) the user's timezone defaults to UTC. When using the HipChat app it displays the local time for the person you are chatting with based upon the timezone for their profile. With everyone on UTC this caused confusion and requires staff to go into the web app to manually set the timezone.

With HipStatus v1.1 we included timezone update support. During each status update the current timezone of the Mac it is running on is applied to the user's HipChat profile. When employees are traveling, the correct timezone will be maintained and users will always know the local time of the person they are chatting with.

## What does it do? ##

HipStatus is a status bar app that updates a user's presence in HipChat based upon their *Office 365* calendar.

![Screenshot](/images/hipstatus.png)

At every 5 minute mark, HipStatus will check both Office 365 and HipChat for the user's current status and then update their availability in HipChat accordingly. HipStatus only updates availability if the user has marked themselves as 'Busy' for the event. If they are 'Free' or have selected 'Tentative', HipStatus will not set their status to busy.

Whenever the app updates a user's status, a notification will appear alerting them. This is a standard OS X notification and the user can manage the appearance of these notifications from System Preferences > Notifications. Turning on OS X's 'Do Not Disturb' mode will also silence HipStatus notifications like any other OS X app.

![Screenshot](/images/dnd_notification.png)

During times where the user does not want their status auto-updated, they can select Pause HipStatus from the menu and then select Resume HipStatus at a later time.

The Office 365 password and HipChat token are saved to the user's keychain. The app's preference file can be found at '~/Library/Preferences/com.jamfw.hipstatus.plist'. For troubleshooting, you can review the app's log file at '~/Library/Logs/HipStatus.log'. You can enable the debugging mode for HipStatus by opening the app using this command:

```
$ open -a /Applications/HipStatus.app/Contents/MacOS/HipStatus --args 1
```

If there are authentications errors when reading the Office 365 or HipChat REST APIs, the user will receive a notification alerting them to the issue. They can click on this notification to display the password/token prompt.

![Screenshot](/images/auth_error_notification.png)

## Customization ##

HipStatus is written in Python and is easily altered, customized and extended.

**Help Ticket and HipChat API Token URLs**

At the top of ```/Contents/Resources/hipstatus.py``` are two global variables that are environment-specific.

The 'ticket_url' should be the URL used for your help desk ticketing system. This is used by two notifications that alert the user when there appears to be an issue with Office 365 or HipChat. Clicking the notification will bring the user to the URL specified in their default browser.

'hipchat_apitoken_url' is used by the HipChat API Token prompt and preferences menu option to take a user to the page where they can generate or retrieve their personal API token. If you are hosted, that URL would be something like: https://myorg.hipchat.com/account/api

**Internal HipChat Server**

You can point to an internal HipChat server if you do not use their hosted offering. In ```hipstatus.py``` line 30, you can enter your sever address as such:

```
self.hipchat = HipChat(self.keychain.read_token(), api='https://hipchat.my.org')
```

Also update the `hipchat_apitoken_url` value accordingly.

**Prompt and Notification Text**

Throughout ```hipstatus.py``` you will find calls to ```rumps.Window()``` and ```rumps.notification()``` that display alerts and prompts to the user. You can modify the text in these calls to your liking.

**Bundle ID, Name and Icons**

You can further customize HipStatus be changing the bundle ID (default is 'com.jamfsw.hipstatus'), the name of the app and the icons used.

In the file ```/Contents/Resources/Info.plist``` is a key for 'CFBundleIdentifier'. Change this to the desired value. Then open ```/Contents/Resources/preferences/__init__.py``` and update the strings containing the bundle ID to this new value on these lines: 18, 22, 30 and 54. Do the same for ```/Contents/Resources/keychain/__init__.py``` for these lines: 12, 16, 27 and 31.

To change the name of the app when it is built, open ```setup.py``` and on line 42 update the 'name' value to the new name of the app.

You can replace ```icon.icns``` with any other .icns file you want as long as the name remains the same. The icons used by HipStatus are all contained within ```/Contents/Resources/```. You can update these icons with your own versions while maintaining the filenames (if you want to change the filenames you will need to update the code in ```hipstatus.py``` accordingly).

Replace these files with your own icons:

```
/Contents/Resources/
    |_ menu_bar_64_black_paused.png
    |_menu_bar_64_black_running.png
    |_menu_bar_64_white_paused.png
    |_menu_bar_64_white_running.png
```

## How to build and deploy this app ##

HipStatus is a status bar app. It runs an update task every 5 minutes at the 5 minute marks. From the menu bar, there are options for pausing and resuming status updates, and a sub-menu for updating the user's status message when busy, email address, Office 365 password and HipChat API token.

HipStatus's status is shown by the icon in the menu bar (a green play badge if running, an orange pause badge if paused).

Saved passwords are stored in the user's login keychain. Preferences are stored in '~/Library/Preferences/com.jamfsw.hipstatus.plist'. The application log is stored in '~/Library/Logs/HipStatus.log'.

To deploy HipStatus as a production app complete the following steps:

Set up a build environment (our recommendation is a clean install of OS X 10.9.5 in a VM). Copy over the source files for HipStatus and the icon file to an appropriate location on the build OS (all source files should be kept within the same directory, for example: 'ROOT/development/<source-files>').

Your build directory should look like this:

```
build-dir/
    |__ Contents/ << This is the application contents
    |__ icon.icns
    |__ Info.plist
    |__ setup.py
```

You will need to install the 'pip' utility to install the dependencies listed above:

```
sudo easy_install pip
```

Now install the packages from **requirements.txt**:

```
sudo pip install -r /path/to/requirements.txt
```

Once the requirements have been installed, the app bundle can be built. 'cd' to the source directory and run:

```
sudo python setup.py py2app --iconfile icon.icns--plist Info.plist
```

Two new directories will have been created in this process: build and dist. Within dist will be HipStatus.app. Copy this app to a system containing your Developer ID Application certificate (this is the certificate used for signing applications).

Use the 'codesign' command to sign the new app:

```
codesign --force --deep --verify --verbose --sign "Developer ID Application: <YOUR ID>" /path/to/HipStatus.app
```

Note that the '--deep' option is only present on OS X 10.10+ and not older versions.

## License ##

```
Copyright (c) 2015, JAMF Software, LLC. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of
      conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.
    * Neither the name of the JAMF Software, LLC nor the names of its contributors may be
      used to endorse or promote products derived from this software without specific prior
      written permission.

THIS SOFTWARE IS PROVIDED BY JAMF SOFTWARE, LLC "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE, LLC BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
