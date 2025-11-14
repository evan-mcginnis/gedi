#
# M A K E F I L E
#
dummy:
	echo "No target specified"

clean:
	rm -rf *.log*

requirements:
	pipreqs

# Pass the location tuple like so
# make SOURCE=/cygdrive/d/GEDI/data summary LOCATION="(32.0, -111.4)" LENGTH=100
summary:
	$(eval _SOURCE = `cygpath -w $(SOURCE)`)
	python biomass.py -s -f $(_SOURCE) --location "$(LOCATION)" --length $(LENGTH) --target MU
