NAME?=grip-tools

INSTALL_BIN_FILES=						\
	grip-announced-pfxs-probe-ips-missing.sh		\
	grip-bgpview-consumers-install.sh			\
	grip-kafka-install.sh				\
	grip-redis-adjacencies-missing.sh			\
	grip-redis-backup.sh				\
	grip-redis-bootstrap-data.sh			\
	grip-redis-install.sh				\
	grip-redis-pfx2as-newcomer-bootstrap.sh		\
	grip-redis-pfx2as-newcomer-missing.sh		\
	grip-redis-pfx2as-historical-date.sh		\
	grip-redis-pfx2as-historical-missing.sh		\
	grip-redis-restore.sh				\
	grip-swift-archiver.pl				\
	grip-tools-selfupdate.sh				\
	bgpview-server-grip-run.sh

INSTALL_BGPVIEW_CONFIG_FILES=					\
	bgpview-consumer-spec.grip.yml

INSTALL_CONFIG_FILES=						\
	grip.crontab					\
	grip-kafka-server.conf				\
	grip-redis.conf

INSTALL_SYSTEMD_FILES=						\
	grip-active-driver@.service			\
	grip-active-drivers.target			\
	grip-active-collector@.service			\
	grip-active-collectors.target			\
	grip-announced-pfxs-probe-ips-updater.service	\
	grip-inference-collector@.service				\
	grip-inference-collectors.target				\
	grip-tagger@.service				\
	grip-taggers.target				\
	grip-consumer-archiver.service			\
	grip-dashboard.service				\
	grip-failure@.service				\
	grip-redis-updater@.service			\
	grip-redis-updaters.target			\
	bgpview-server-grip.service			\
	redis.service						\
	kafka.service

DIST_FILES=							\
	bin/*							\
	config/*						\
	systemd/*						\
	Makefile

PKG_NAME?=$(NAME)
PKG?=$(PKG_NAME).tar.gz

PREFIX?=/usr/local
PREFIX_BIN?=$(PREFIX)/bin
PREFIX_BGPVIEW_ETC?=$(PREFIX)/etc/bgpview
PREFIX_ETC?=$(PREFIX)/etc/grip
PREFIX_SYSTEMD?=/lib/systemd/system

CONSUMER_TMP?=/tmp/grip-consumer-tmp

all:
	@echo "Select either 'dist', 'clean', or 'install' targets"

$(PKG):
	rm -rf $(PKG_NAME)
	mkdir -p $(PKG_NAME)
	cp -R $(DIST_FILES) $(PKG_NAME)/
	tar zcvf $(PKG) $(PKG_NAME)/
	rm -rf $(PKG_NAME)

dist: $(PKG)

clean:
	rm -f $(PKG)

install:
	@mkdir -p $(PREFIX_BIN)
	@for file in $(INSTALL_BIN_FILES); \
		do install -p --backup=none -v -m 0755 $$file $(PREFIX_BIN)/`basename $$file` || exit $?; \
	done
	@mkdir -p $(PREFIX_BGPVIEW_ETC)
	@for file in $(INSTALL_BGPIEW_CONFIG_FILES); \
		do install -p --backup=none -v -m 0644 $$file $(PREFIX_BGPVIEW_ETC)/`basename $$file` || exit $?; \
	done
	@mkdir -p $(PREFIX_ETC)
	@for file in $(INSTALL_CONFIG_FILES); \
		do install -p --backup=none -v -m 0644 $$file $(PREFIX_ETC)/`basename $$file` || exit $?; \
	done
	@mkdir -p $(PREFIX_SYSTEMD)
	@for file in $(INSTALL_SYSTEMD_FILES); \
		do install -p --backup=none -v -m 0644 $$file $(PREFIX_SYSTEMD)/`basename $$file` || exit $?; \
	done
	@mkdir -p $(CONSUMER_TMP)
	@chown -R bgp:bgp $(CONSUMER_TMP)

.PHONY: dist clean install
