SHELL=/bin/bash

SCHED=sessions/${SESSION}/EVNSchedule.txt
SESSION=sessions/May-Jun21
SESSION=`dirname ${SCHED}`
LOGDIR=${SESSION}/logs

#check_dir:
#	-mkdir -p ${LOGDIR}

dw_example:
	scp oper@fs6:/usr2/log/gm076tr.log log

dw_rxg:
	-mkdir -p ${SESSION}/rxg_files
	scp -p  oper@fs6:/usr2/control/rxg_evn/*.rxg ${SESSION}/rxg_files
	cd ${SESSION}/rxg_files && for f in `ls *.rxg`; do dst=`echo $$f | sed -e "s/\b\(.\)/\u\1/"`; mv $$f $$dst; done

plot_rxg:
	cd ${SESSION}/rxg_files && less Trl.rxg|grep rcp |awk 'NR>3 && NR<65 {print NR,$$2,$$3}'  | python3 ~/programy/cpems/pyth/plot_function.py stdin -x 1 -y 2 --xlabel 'freq [MHz]' --ylabel 'Tcal RCP [K]' --title `date +%Y-%m-%d` -o Trl-RCP-`date +%Y-%m-%d`.rxg.jpg --save --show
	cd ${SESSION}/rxg_files && less Trl.rxg|grep lcp |awk 'NR>3 && NR<65 {print NR,$$2,$$3}'  | python3 ~/programy/cpems/pyth/plot_function.py stdin -x 1 -y 2 --xlabel 'freq [MHz]' --ylabel 'Tcal LCP [K]' --title `date +%Y-%m-%d` -o Trl-LCP-`date +%Y-%m-%d`.rxg.jpg --save --show

logs: projs dw_logs clean_logs fix_logs

dirs:
	-mkdir -p ${LOGDIR}

projs: dirs
	@dos2unix ${SCHED}
	cat ${SCHED} |  awk 'BEGIN {st=1e10; NPROJ=0}; $$2=="PROJECT" && $$3=="INFORMATION" { st=NR+4}; NR>st && $$1=="" && NPROJ>0 { exit}; NR>st && $$1!="" {print tolower($$1); NPROJ=NPROJ+1}; ' > ${LOGDIR}/projects
	ln -sf ${LOGDIR}/projects 
	@echo "There are "`cat projects |wc -l`" projects in this session"
	cat ${LOGDIR}/projects

dw_logs:
	-for l in `cat projects`; do  scp oper@fs6:/usr2/log/$$l"tr".log ${LOGDIR} ; done
#	scp oper@fs6:/usr2/log/n21k2.log ${LOGDIR}/logs
#	 projects ${LOGDIR}

clean_logs:
	cd ${LOGDIR} && for l in `ls *.log`; do echo $$l;  sed -e '/,$$$$$$$$$$,/d' $$l | grep -v caltemp > $$l.clean ;  mv  $$l.clean  $$l; done
#	cd ${LOGDIR} && for l in `ls *.log`; do echo $$l;  sed -e '/,$$$$$,/p' $$l ; exit ;  done
#	cd ${LOGDIR} && sed -n -e '/,$$$$$$$$$$,/p' n21l2tr.log

fix_logs:
	cd ${LOGDIR} && for l in `ls *.log`; do echo $$l;  python ../../../fix-tsys.py $$l > $$l.fixed ;  mv  $$l.fixed  $$l; done

check_venv:
	source venv/bin/activate
antab: 
	. venv/bin/activate && cd ${LOGDIR} && for l in `ls *.log`; do  ../../../antabfs_tassili.sh $$l; done

archive_rxg:
	-rm -r ${LOGDIR}/rxg_files
	cp -rp data/rxg_files  ${LOGDIR}/rxg_files-`date +%Y-%m-%d`

export_antabs:
	cd ${SESSION} && ../../export_antabs.sh `basename ${SCHED}`

export_trainset:
	./export_trainset.sh
