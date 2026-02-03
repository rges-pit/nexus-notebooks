This is an optional feature used to define the "splash" page which is displayed
once a notebook user session actually started,   typically a high level tutorial
and description of the platform in an intro.md file and/or related files under
content/.

Right now when you select the RGES image on the RNN you get the RNN intro page.
The idea here is that RGES can have it's own unique page with whatever you want.

To understand better just start a RNN session with the default image or look
here:  https://github.com/spacetelescope/roman_notebooks/blob/main/content/intro.md

This is an option not a requirement,  let STScI/Octarine know if you'd like
to pursue this and we can override the configuration of the RGES image profile
to select your version instead of the RNN version.

The format of your splash page is up to you but the RNN and tike_content
notebook repos cn serve as examples.

TODO: replace this file with your own intro.md or remove the content/ directory
tree.
