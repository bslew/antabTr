SHELL=/bin/bash

PLOT_FN=~/programy/cpems/pyth/venv-ubuntu20/bin/plot_function.py
SCHED=sessions/${SESSION}/EVNSchedule.txt
SESSION=sessions/May-Jun21
SESSION=`dirname ${SCHED}`
LOGDIR=${SESSION}/logs
VENV=venv

#check_dir:
#	-mkdir -p ${LOGDIR}

install: 
	@echo "Installing python package"
	source ${VENV}/bin/activate && cd python3 && python setup.py install
	source ${VENV}/bin/activate && cp sh/share_wisdom.sh ${VENV}/bin

	@echo "Installing scripts"
	install sh/antabTr.sh venv/bin/
	install sh/export_antabs.sh venv/bin/

	@echo "Installing config file"
	-mkdir -p $(HOME)/.config/antabfs/
	@echo "This will override your current config file ($(HOME)/.config/antabfs/antabfs.ini)."
	@echo "The original file will be moved to $(HOME)/.config/antabfs/antabfs.ini.bak"
	@echo "Press enter to continue..."
	@read
	@if [ -f $(HOME)/.config/antabfs/antabfs.ini ]; then mv $(HOME)/.config/antabfs/antabfs.ini $(HOME)/.config/antabfs/antabfs.ini.bak ; fi
	cp antabfs.ini $(HOME)/.config/antabfs/antabfs.ini
	@echo "done"


help:
	@echo ""
	@echo "USAGE"
	@echo ""
	@echo ""
	@echo "Example of typical antab session"
	@echo ""
	@echo "place your schedule to a new directory and type:"
	@echo "make SCHED=sessions/jan22/eEVN-180122.txt dw_rxg"
	@echo "make SCHED=sessions/jan22/eEVN-180122.txt plot_rxg"
	@echo "make SCHED=sessions/jan22/eEVN-180122.txt logs"
	@echo "make SCHED=sessions/jan22/eEVN-180122.txt antab"
	@echo "make SCHED=sessions/jan22/eEVN-180122.txt export_antabs"
	@echo ""
	@echo ""

dw_example:
	scp oper@fs6:/usr2/log/gm076tr.log log

dw_rxg:
	-mkdir -p ${SESSION}/rxg_files/tmp
	scp -p  oper@fs6:/usr2/control/rxg_evn/*.rxg ${SESSION}/rxg_files/tmp
	cd ${SESSION}/rxg_files/tmp && for f in `ls *.rxg`; do dst=`echo $$f | sed -e "s/\b\(.\)/\u\1/"`; mv $$f ../$$dst; done

plot_rxg:
	cd ${SESSION}/rxg_files && less Trl.rxg|grep ^rcp |awk 'NF==3 {print NR,$$2,$$3}'  | ${PLOT_FN} stdin -x 1 -y 2 --xlabel 'freq [MHz]' --ylabel 'Tcal RCP [K]' --title `date +%Y-%m-%d` -o Trl-RCP-`date +%Y-%m-%d`.rxg.jpg --save --show
	cd ${SESSION}/rxg_files && less Trl.rxg|grep ^lcp |awk 'NF==3 {print NR,$$2,$$3}'  | ${PLOT_FN} stdin -x 1 -y 2 --xlabel 'freq [MHz]' --ylabel 'Tcal LCP [K]' --title `date +%Y-%m-%d` -o Trl-LCP-`date +%Y-%m-%d`.rxg.jpg --save --show

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
	. ${VENV}/bin/activate && cd ${LOGDIR} && for l in `ls *.log`; do echo $$l; fix-tsys.py $$l > $$l.fixed ;  mv  $$l.fixed  $$l; done

check_venv:
	source ${VENV}/bin/activate
antab: 
#	. ${VENV}/bin/activate && cd ${LOGDIR} && for l in `ls *.log`; do antabTr.sh $$l ${VERB}; done
	. ${VENV}/bin/activate && cd ${LOGDIR} && for l in `ls *.log`; do echo "Processing $$l"; antabTr.py --clean rlm $$l ${VERB}; done

#archive_rxg:
#	-rm -r ${LOGDIR}/rxg_files
#	cp -rp data/rxg_files  ${LOGDIR}/rxg_files-`date +%Y-%m-%d`

export_antabs:
	. ${VENV}/bin/activate && cd ${SESSION} && export_antabs.sh `basename ${SCHED}`

share_wisdom:
	./share_wisdom.sh
