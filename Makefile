
.PHONY: requirements
requirements:
	python -m venv $(DESTDIR)/share/consolesnake/venv
	. $(DESTDIR)/share/consolesnake/venv/bin/activate && pip install -r requirements.txt

.PHONY: install
install:
	install -d ${DESTDIR}/share/consolesnake/Networking ${DESTDIR}/share/consolesnake/Maps ${DESTDIR}/share/consolesnake/Resources ${DESTDIR}/bin/
	install game_tui.py game_client.py game_server.py game.py ${DESTDIR}/share/consolesnake/
	install Resources/*.py ${DESTDIR}/share/consolesnake/Resources/
	install Networking/*.py ${DESTDIR}/share/consolesnake/Networking/
	install Maps/*.py ${DESTDIR}/share/consolesnake/Maps/

	sed "s|{INSTALL_DIR_PLACEHOLDER}|$(DESTDIR)|g" bin/consolesnake.template > $(DESTDIR)/bin/consolesnake
	sed "s|{INSTALL_DIR_PLACEHOLDER}|$(DESTDIR)|g" bin/consolesnake-server.template > $(DESTDIR)/bin/consolesnake-server
	chmod +x $(DESTDIR)/bin/consolesnake $(DESTDIR)/bin/consolesnake-server

uninstall:
	rm -r -I ${DESTDIR}/share/consolesnake
	rm -i ${DESTDIR}/bin/consolesnake*
