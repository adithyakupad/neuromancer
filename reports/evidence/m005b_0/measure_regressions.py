"""Bounded repeat solely to resolve missing regression-process RSS measurement."""
import json,re,subprocess,sys
from pathlib import Path
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check()
 command=['/usr/bin/time','-l',sys.executable,'-m','pytest','-q','--basetemp='+str(R/'measured_regression_fixtures'),'--junitxml='+str(R/'measured_regression_tests.xml')]
 with (R/'measured_regressions.log').open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=max(.1,d.remaining()-.8))
 text=(R/'measured_regressions.log').read_text();peak=int(re.search(r'(\d+)\s+maximum resident set size',text).group(1));assert result.returncode==0 and peak<2*1024**3
 (R/'regression_resource.json').write_text(json.dumps(dict(status='PASS',returncode=result.returncode,peak_rss_bytes=peak,tool='/usr/bin/time -l',scope='pytest process high-water, not simultaneous descendant aggregate',reason='First full regression run did not measure RSS; this repeat resolves that resource audit gap',command=command),indent=2)+'\n');d.check()
if __name__=='__main__':main()
