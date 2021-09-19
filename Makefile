requirements:
	pip3 install -r requirements.txt

install:
	install -d ${DESTDIR}/usr/share/consolesnake/Networking ${DESTDIR}/usr/share/consolesnake/Maps ${DESTDIR}/usr/share/consolesnake/Resources ${DESTDIR}/usr/bin/
	install game_tui.py game_client.py game_server.py game.py ${DESTDIR}/usr/share/consolesnake/
	install Resources/* ${DESTDIR}/usr/share/consolesnake/Resources/
	install Networking/* ${DESTDIR}/usr/share/consolesnake/Networking/
	install Maps/* ${DESTDIR}/usr/share/consolesnake/Maps/

	install bin/consolesnake ${DESTDIR}/usr/bin/
	install bin/consolesnake-server ${DESTDIR}/usr/bin/

uninstall:
	rm -r -I ${DESTDIR}/usr/share/consolesnake
	rm -i ${DESTDIR}/usr/bin/consolesnake*
	rm -r -I ${HOME}/.local/share/consolesnake
