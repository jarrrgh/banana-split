Example Extension
=================

This is an example extension plug-in for Uranium. Uranium is the underlying framework used in Ultimaker Cura and NinjaKittens.

The extension type plug-in is a "generic" type of plug-in that just gets some object constructed upon loading the plug-in for the first time. Using the initialisation of that class as starting point for your code, you can access all of the application.

There are two typical use cases for extensions:
1. Modifying some behaviour in the application or modifying current functionality. This is done by listening to the desired event, such as the changing of the current machine or on start-up. When that event happens, some code can be executed that adds on the behaviour.
2. Adding a dialogue that provides additional functionality. There is a handy built-in method that allows you to add a menu item easily, and what should happen when the user clicks on it.

This plug-in shows an example of both use cases.

Packaging
---------

To package your plug-in, compress your plug-in folder in a .zip archive and rename that archive to get the `.plugin` extension. These .plugin files can be dropped into any Uranium application to be installed.
