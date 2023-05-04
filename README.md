Banana Split
=================

Imagine splitting a banana neatly in half with quick swing of a katana. That's how easy it's now to split your model in Cura. Although technically splitting is not what really happens.

The tool actually duplicates a selected model, flips it around, and then actively mirrors the Z value in relation to the build plate—sort of like a seesaw. Here's how to use it:

1. Position your model in a way that roughly half of the model goes below the build plate.
2. Press Split button, and the tool will reflect anything below the surface on top of it.
3. Move your original model along the Z axis to fine tune your cut real-time.

Serving
---------

See the serve.sh for deployment. It works on my Mac at least. Update the PLUGINS_PATH to match the version of your Cura installation. Note: the deployment will shutdown any running Cura instances.
