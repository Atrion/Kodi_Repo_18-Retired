from resources.lib.externals.hachoir.hachoir_metadata.version import VERSION as __version__
from resources.lib.externals.hachoir.hachoir_metadata.metadata import extractMetadata

# Just import the module,
# each module use registerExtractor() method
import resources.lib.externals.hachoir.hachoir_metadata.archive
import resources.lib.externals.hachoir.hachoir_metadata.audio
import resources.lib.externals.hachoir.hachoir_metadata.file_system
import resources.lib.externals.hachoir.hachoir_metadata.image
import resources.lib.externals.hachoir.hachoir_metadata.jpeg
import resources.lib.externals.hachoir.hachoir_metadata.misc
import resources.lib.externals.hachoir.hachoir_metadata.program
import resources.lib.externals.hachoir.hachoir_metadata.riff
import resources.lib.externals.hachoir.hachoir_metadata.video

