# Bước 9 – Stress/Spike fixed smoke verification

**Kết quả: PASS** cho defaults native, Stress/Spike smoke 1 VU, và stress stage smoke. Java 17/JMeter 5.6.3; mỗi JMeter invocation timeout 90s; SUT được reset ngay trước từng run. Không chạy nhiều VU và không tạo/sửa thủ công JTL. `AI_LOG.md` không đổi.

## Native defaults (GroovyMain, throwaway command)

Exact invocation (executed in the repository root):

```sh
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
JM=$HOME/tools/apache-jmeter-5.6.3
CP="$JM/lib/*:$JM/lib/ext/*"
java -cp "$CP" groovy.ui.GroovyMain -e 'import org.apache.jmeter.util.JMeterUtils; import org.apache.jmeter.engine.util.CompoundVariable; import groovy.xml.XmlSlurper; JMeterUtils.loadJMeterProperties(System.getProperty("user.home")+"/tools/apache-jmeter-5.6.3/bin/jmeter.properties"); def props=JMeterUtils.getJMeterProperties(); ["threads","loops","stage_smoke"].each{props.remove(it)}; def x=new XmlSlurper().parse(new File("test-plans/23120190_Stress_20261117.jmx")); def expr=x."**".findAll{it.name()=="ThreadGroup"}.collect{it.stringProp.find{it.@name=="ThreadGroup.num_threads"}.text()}; assert expr.size()==4; assert expr.collect{new CompoundVariable(it).execute()}==["50","100","200","290"]; assert props.getProperty("threads")==null; props.setProperty("threads","5");props.setProperty("loops","2"); assert expr.collect{new CompoundVariable(it).execute()}==["5","0","0","0"];props.setProperty("stage_smoke","true");assert expr.collect{new CompoundVariable(it).execute()}==["5","5","5","5"]; println(expr); println("native assertions passed")'
```

Output showed the four source expressions in order: `${__P(threads,50)}`, then three native `${__groovy(...)}` expressions; `native assertions passed`. Assertions confirmed defaults `50/100/200/290`, absent `threads` property remains null, properties `threads=5, loops=2` produce `5/0/0/0`, and additionally `stage_smoke=true` produces `5/5/5/5`. The first invocation failed because its shell assignment did not expand `CLASSPATH`; corrected to explicit `CP` above. No persistent script was created.

## Stress and Spike one-thread/one-loop smokes

```sh
scripts/reset_sut.sh
# with Java 17 exports as above
 timeout 90s $HOME/tools/apache-jmeter-5.6.3/bin/jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l results/smoke/step9_stress_20261117.jtl > results/smoke/step9_stress_20261117.log 2>&1

scripts/reset_sut.sh
timeout 90s $HOME/tools/apache-jmeter-5.6.3/bin/jmeter -n -t test-plans/23120190_Spike_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -l results/smoke/step9_spike_20261117.jtl > results/smoke/step9_spike_20261117.log 2>&1
```

Both commands exited 0. Each JTL contains precisely 7 main samples, one each: `01 Login`, `02 Products`, `03 Product detail`, `04 Add cart`, `05 Get cart`, `06 Checkout`, `07 My orders`. All returned HTTP 200 with `success=true`; each log summary reports `7` and `Err: 0 (0.00%)`; no ERROR/Exception was found.

## Stage smoke

```sh
scripts/reset_sut.sh
timeout 90s $HOME/tools/apache-jmeter-5.6.3/bin/jmeter -n -t test-plans/23120190_Stress_20261117.jmx -Jthreads=1 -Jrampup=1 -Jloops=1 -Jstage_smoke=true -Jlock_percent=100 -l results/smoke/step9_stress_gate_20261117.jtl > results/smoke/step9_stress_gate_20261117.log 2>&1
```

Exit 0; actual JTL has 32 samples, exactly 28 main samples (7 in each of four stages) plus four `Negative login` samples, all HTTP 401 with JTL `success=true`. All 28 main samples were HTTP 200 and `success=true`; total JMeter summary: 32, `Err: 0 (0.00%)`. The expected 4 negative responses were 401 (no 403 samples in this one-iteration run). JMeter output did not contain `STRESS_GATE` or `STRESS_STAGE_START` records, so the gate-specific assertion (previous-stage sample counts of 7—not 8—and `continue=true`) is **not verified from these logs**, despite all 32 samples succeeding. Do not infer those gate fields from JTL alone.

**Sources:** actual JTLs and captured JMeter output under `results/smoke/step9_*_20261117.{jtl,log}`; exact expressions parsed directly from `test-plans/23120190_Stress_20261117.jmx`. The console Groovy classpath correction is documented above; no test was rerun to reconfirm a test failure.
