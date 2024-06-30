install:
	@pip install \
	-r requirements.txt \
	-r requirements-dev.txt

compile:
	@rm -f requirements*.txt
	@pip-compile -v pyproject.toml \
 	--unsafe-package pyobjc-core \
 	--unsafe-package pyobjc-framework-cocoa \
 	--unsafe-package pyobjc-framework-security \
 	--unsafe-package pyobjc-framework-webkit
	@pip-compile -o requirements-dev.txt --extra dev \
 	--unsafe-package pyobjc-core \
 	--unsafe-package pyobjc-framework-cocoa \
 	--unsafe-package pyobjc-framework-security \
 	--unsafe-package pyobjc-framework-webkit \
 	pyproject.toml

sync:
	@pip-sync requirements*.txt

mount:
	-./mount.sh	 # Must define your own mount.sh