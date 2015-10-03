
all : base.zip

base.zip :
	-rm base.zip 2> /dev/null
	cd base_install ; 7z a ../base.zip .

.PHONY: all base.zip
