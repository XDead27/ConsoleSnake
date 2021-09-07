requirements:
	pip3 install -r requirements.txt

install:
	install -d /usr/share/consolesnake/Networking /usr/share/consolesnake/Maps /usr/share/consolesnake/Resources
	install game_tui.py game_client.py game_server.py game.py /usr/share/consolesnake/
	install Resources/* /usr/share/consolesnake/Resources/
	install Networking/* /usr/share/consolesnake/Networking/
	install Maps/* /usr/share/consolesnake/Maps/

	install bin/consolesnake.sh /usr/bin/consolesnake
	install bin/consolesnake-server.sh /usr/bin/consolesnake-server

uninstall:
	rm -r -I /usr/share/consolesnake
	rm -i /usr/bin/consolesnake*
