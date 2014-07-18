DESTDIR=/

all:
	echo "Nothing to compile"

install:
	mkdir -p $(DESTDIR)/etc/cloudOver/
	cp -r etc/coreDavConf $(DESTDIR)/etc/cloudOver/

	mkdir -p $(DESTDIR)/usr/lib/cloudOver/
	cp -r lib/overCluster $(DESTDIR)/usr/lib/cloudOver/

	mkdir -p $(DESTDIR)/var/lib/cloudOver/coreDav/
	mkdir -p $(DESTDIR)/var/log/cloudOver/coreDav/
	mkdir -p $(DESTDIR)/var/run/

	mkdir -p $(DESTDIR)/etc/apache2/sites-available/

	# Modern apache versions
	#ln -s /etc/cloudOver/coreDavConf/apache-sites/coreDav $(DESTDIR)/etc/apache2/sites-available/coreDav.conf

	# Old apache versions
	ln -s /etc/cloudOver/coreDavConf/apache-sites/coreDav $(DESTDIR)/etc/apache2/sites-available/coreDav
