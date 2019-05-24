TARGET=Textures.xbt

all: $(TARGET)

.PHONY: force

$(TARGET):
	/home/pi/build/xbmc/tools/depends/native/TexturePacker/bin/TexturePacker -dupecheck -input . -output $(TARGET)

clean:
	rm -f $(TARGET)

distclean: clean

