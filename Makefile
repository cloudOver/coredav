DESTDIR=/

all:
	echo "Nothing to compile"

install:
	mkdir -p $(DESTDIR)/etc/cloudOver/
	cp -r etc/overClusterConf $(DESTDIR)/etc/cloudOver/

	mkdir -p $(DESTDIR)/usr/lib/cloudOver/
	cp -r lib/overCluster $(DESTDIR)/usr/lib/cloudOver/

	mkdir -p $(DESTDIR)/usr/
	cp -r sbin/ $(DESTDIR)/usr/
	
	mkdir -p $(DESTDIR)/var/lib/cloudOver/overCluster/
	mkdir -p $(DESTDIR)/var/log/cloudOver/overCluster/
	mkdir -p $(DESTDIR)/var/run/

	mkdir -p $(DESTDIR)/etc/apache2/sites-available/

	# Modern apache versions
	#ln -s /etc/cloudOver/overClusterConf/apache-sites/overCluster-api $(DESTDIR)/etc/apache2/sites-available/overCluster-api.conf
	#ln -s /etc/cloudOver/overClusterConf/apache-sites/overCluster-ci $(DESTDIR)/etc/apache2/sites-available/overCluster-ci.conf

	# Old apache versions
	ln -s /etc/cloudOver/overClusterConf/apache-sites/overCluster-api $(DESTDIR)/etc/apache2/sites-available/overCluster-api
	ln -s /etc/cloudOver/overClusterConf/apache-sites/overCluster-ci $(DESTDIR)/etc/apache2/sites-available/overCluster-ci