SHELL=/bin/bash

SCHEDULE=sessions/May-Jun21/EVNSchedule.txt
LOGDIR=`dirname ${SCHEDULE}`
dw_example:
	scp oper@fs6:/usr2/log/gm076tr.log log

dw_rxg:
	scp  oper@fs6:/usr2/control/rxg_evn/*.rxg data/rxg_files
	cd data/rxg_files && for f in `ls *.rxg`; do dst=`echo $$f | sed -e "s/\b\(.\)/\u\1/"`; mv $$f $$dst; done


logs: dw_logs clean_logs fix_logs
dw_logs:
	@dos2unix ${SCHEDULE}
	@cat ${SCHEDULE} | awk 'BEGIN {st=1e10}; $$2=="PROJECT" && $$3=="INFORMATION" { st=NR+4}; NR>st && $$1=="" { exit}; NR>st {print tolower($$1)}; ' > projects
	@echo "There are "`cat projects |wc -l`"projects in this session"
	mkdir -p ${LOGDIR}/logs
	for l in `cat projects`; do  scp oper@fs6:/usr2/log/$$l"tr".log ${LOGDIR}/logs ; done
#	scp oper@fs6:/usr2/log/n21k2.log ${LOGDIR}/logs


clean_logs:
	cd ${LOGDIR}/logs && for l in `ls *.log`; do echo $$l;  sed -e '/,$$$$$$$$$$,/d' $$l | grep -v caltemp > $$l.clean ;  mv  $$l.clean  $$l; done
#	cd ${LOGDIR}/logs && for l in `ls *.log`; do echo $$l;  sed -e '/,$$$$$,/p' $$l ; exit ;  done
#	cd ${LOGDIR}/logs && sed -n -e '/,$$$$$$$$$$,/p' n21l2tr.log

fix_logs:
	cd ${LOGDIR}/logs && for l in `ls *.log`; do echo $$l;  python ../../../fix-tsys.py $$l > $$l.fixed ;  mv  $$l.fixed  $$l; done

antab:
	cd ${LOGDIR}/logs && for l in `ls *.log`; do ../../../antabfs_tassili.sh $$l; done
