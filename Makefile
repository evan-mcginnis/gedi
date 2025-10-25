#
# M A K E F I L E
#
dummy:
	echo "No target specified"

clean:
	rm -rf *.log*

requirements:
	pipreqs

summary:
	$(eval _SOURCE = `cygpath -w $(SOURCE)`)
	python biomass.py -s -f $(_SOURCE)
