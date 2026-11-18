#!/usr/bin/env python3
"""Build a JMeter .jmx for one endpoint group from a JSON definition (stdlib only).

Usage: gen_plan.py <group.json> <out.jmx>
Threads/ramp/duration are left as ${__P(...)} so the same plan serves every profile.
CSV paths are made absolute (resolved from the current dir = project root),
because JMeter resolves relative paths against the .jmx folder.
No listener is added on purpose: results are written once by `jmeter -l`
(a second ResultCollector writing the same file would duplicate every sample).
"""
import json
import os
import sys
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent


def prop(parent, kind, name, value):
    e = SubElement(parent, kind, name=name)
    e.text = str(value).lower() if isinstance(value, bool) else str(value)
    return e


def node(tree, tag, testclass, guiclass, name, props=()):
    """Append a test element plus its sibling <hashTree>; return (element, child hashTree)."""
    e = SubElement(tree, tag, guiclass=guiclass, testclass=testclass, testname=name)
    for kind, key, value in props:
        prop(e, kind, key, value)
    return e, SubElement(tree, 'hashTree')


def header_manager(tree, name, headers):
    e, _ = node(tree, 'HeaderManager', 'HeaderManager', 'HeaderPanel', name)
    coll = SubElement(e, 'collectionProp', name='HeaderManager.headers')
    for k, v in headers.items():
        h = SubElement(coll, 'elementProp', name=k, elementType='Header')
        prop(h, 'stringProp', 'Header.name', k)
        prop(h, 'stringProp', 'Header.value', v)


def sampler(tree, step):
    props = [('boolProp', 'HTTPSampler.use_keepalive', True),
             ('stringProp', 'HTTPSampler.path', step['path']),
             ('stringProp', 'HTTPSampler.method', step['method'])]
    e, child = node(tree, 'HTTPSamplerProxy', 'HTTPSamplerProxy', 'HttpTestSampleGui', step['label'], props)
    if 'body' in step:
        prop(e, 'boolProp', 'HTTPSampler.postBodyRaw', True)
        args = SubElement(e, 'elementProp', name='HTTPsampler.Arguments', elementType='Arguments')
        arg = SubElement(SubElement(args, 'collectionProp', name='Arguments.arguments'),
                         'elementProp', name='', elementType='HTTPArgument')
        prop(arg, 'boolProp', 'HTTPArgument.always_encode', False)
        prop(arg, 'stringProp', 'Argument.value', json.dumps(step['body'], ensure_ascii=False)
             if not isinstance(step['body'], str) else step['body'])
        prop(arg, 'stringProp', 'Argument.metadata', '=')
    if step.get('auth'):
        header_manager(child, 'Bearer token', {'Authorization': 'Bearer ${token}'})
    # Status-code check decides success, so an expected 401/403 counts as success.
    a, _ = node(child, 'ResponseAssertion', 'ResponseAssertion', 'AssertionGui', 'Expect ' + step['expect'],
                [('stringProp', 'Assertion.test_field', 'Assertion.response_code'),
                 ('boolProp', 'Assertion.assume_success', True),
                 ('intProp', 'Assertion.test_type', 1)])
    coll = SubElement(a, 'collectionProp', name='Asserion.test_strings')
    prop(coll, 'stringProp', '0', step['expect'])
    for var, path in step.get('extract', {}).items():
        node(child, 'JSONPostProcessor', 'JSONPostProcessor', 'JSONPostProcessorGui', 'Extract ' + var,
             [('stringProp', 'JSONPostProcessor.referenceNames', var),
              ('stringProp', 'JSONPostProcessor.jsonPathExprs', path),
              ('stringProp', 'JSONPostProcessor.match_numbers', '1'),
              ('stringProp', 'JSONPostProcessor.defaultValues', 'NOT_FOUND')])


def build(group):
    root = Element('jmeterTestPlan', version='1.2', properties='5.0', jmeter='5.6.3')
    top = SubElement(root, 'hashTree')
    tp, plan = node(top, 'TestPlan', 'TestPlan', 'TestPlanGui', 'Endpoint group: ' + group['name'],
                    [('boolProp', 'TestPlan.functional_mode', False),
                     ('boolProp', 'TestPlan.serialize_threadgroups', False)])
    udv = SubElement(tp, 'elementProp', name='TestPlan.user_defined_variables', elementType='Arguments',
                     guiclass='ArgumentsPanel', testclass='Arguments', testname='User Defined Variables')
    coll = SubElement(udv, 'collectionProp', name='Arguments.arguments')
    for k, v in (('HOST', '${__P(host,localhost)}'), ('PORT', '${__P(port,3000)}')):
        arg = SubElement(coll, 'elementProp', name=k, elementType='Argument')
        prop(arg, 'stringProp', 'Argument.name', k)
        prop(arg, 'stringProp', 'Argument.value', v)
        prop(arg, 'stringProp', 'Argument.metadata', '=')
    node(plan, 'ConfigTestElement', 'ConfigTestElement', 'HttpDefaultsGui', 'HTTP Request Defaults',
         [('stringProp', 'HTTPSampler.domain', '${HOST}'), ('stringProp', 'HTTPSampler.port', '${PORT}'),
          ('stringProp', 'HTTPSampler.protocol', 'http'), ('stringProp', 'HTTPSampler.connect_timeout', '5000'),
          ('stringProp', 'HTTPSampler.response_timeout', '30000')])
    header_manager(plan, 'JSON headers', {'Content-Type': 'application/json'})

    tg, tgt = node(plan, 'ThreadGroup', 'ThreadGroup', 'ThreadGroupGui', group['name'] + ' users',
                   [('stringProp', 'ThreadGroup.on_sample_error', 'continue'),
                    ('stringProp', 'ThreadGroup.num_threads', '${__P(threads,20)}'),
                    ('stringProp', 'ThreadGroup.ramp_time', '${__P(rampup,10)}'),
                    ('boolProp', 'ThreadGroup.scheduler', True),
                    ('stringProp', 'ThreadGroup.duration', '${__P(duration,120)}'),
                    ('stringProp', 'ThreadGroup.delay', '0')])
    loop = SubElement(tg, 'elementProp', name='ThreadGroup.main_controller', elementType='LoopController',
                      guiclass='LoopControlPanel', testclass='LoopController')
    prop(loop, 'boolProp', 'LoopController.continue_forever', False)
    prop(loop, 'stringProp', 'LoopController.loops', '-1')

    for csv in group.get('csv', []):
        node(tgt, 'CSVDataSet', 'CSVDataSet', 'TestBeanGUI', 'CSV ' + csv['file'],
             [('stringProp', 'filename', os.path.abspath(csv['file'])), ('stringProp', 'fileEncoding', 'UTF-8'),
              ('stringProp', 'variableNames', csv['vars']), ('boolProp', 'ignoreFirstLine', True),
              ('stringProp', 'delimiter', ','), ('boolProp', 'quotedData', False),
              ('boolProp', 'recycle', True), ('boolProp', 'stopThread', False),
              ('stringProp', 'shareMode', 'shareMode.all')])

    setup = group.get('setup', [])
    if setup:  # e.g. log in once per virtual user, then reuse the token
        _, once = node(tgt, 'OnceOnlyController', 'OnceOnlyController', 'OnceOnlyControllerGui', 'Once per user')
        for step in setup:
            sampler(once, step)
    for step in group['steps']:
        parent = tgt
        if 'percent' in step:
            _, parent = node(tgt, 'ThroughputController', 'ThroughputController', 'ThroughputControllerGui',
                             f"{step['percent']}% {step['label']}",
                             [('intProp', 'ThroughputController.style', 1),
                              ('boolProp', 'ThroughputController.perThread', False),
                              ('stringProp', 'ThroughputController.percentThroughput', step['percent'])])
        sampler(parent, step)
    lo, hi = group.get('think_ms', [500, 1500])
    node(tgt, 'UniformRandomTimer', 'UniformRandomTimer', 'UniformRandomTimerGui', f'Think time {lo}-{hi} ms',
         [('stringProp', 'ConstantTimer.delay', lo), ('stringProp', 'RandomTimer.range', hi - lo)])
    return root


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    group = json.load(open(sys.argv[1], encoding='utf-8'))
    tree = ElementTree(build(group))
    indent(tree)
    tree.write(sys.argv[2], encoding='UTF-8', xml_declaration=True)
    print(f"plan: {sys.argv[2]} ({len(group.get('setup', []))} setup + {len(group['steps'])} steps)")


if __name__ == '__main__':
    main()
