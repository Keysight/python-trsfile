# To use this converter, please install the 'chipwhisperer' and 'scipy' packages from PIPy
import os
import re
from os.path import dirname
from typing import Any

from chipwhisperer.common.api.ProjectFormat import Project

from trsfile import TraceSet, Header, TracePadding, Trace, SampleCoding
from trsfile.parametermap import TraceSetParameterMap, TraceParameterDefinitionMap, TraceParameterMap
from trsfile.traceparameter import TraceParameterDefinition, ParameterType, StringParameter, ByteArrayParameter


def to_trs(path_to_project: str, output_path: str, trace_index: int = 0):
    project = Project()
    project.load(path_to_project)
    container = project.trace_manager().get_segment(trace_index)
    traceset_parameters = TraceSetParameterMap()
    headers = {
        Header.DESCRIPTION: read_or_default(container.config, 'notes'),
        Header.ACQUISITION_DEVICE_ID: read_or_default(container.config, 'scopeName'),
        Header.SCALE_X: 1 / float(read_or_default(container.config, 'scopeSampleRate', 1)),
        Header.TRACE_SET_PARAMETERS: traceset_parameters
    }
    container.loadAllTraces()
    contains_textin = container.textins is not None and len(container.textins) > 0 and container.textins[0] is not None
    contains_keylist = container.keylist is not None and len(container.keylist) > 0 and container.keylist[0] is not None
    contains_textout = container.textouts is not None and len(container.textouts) > 0 and container.textouts[0] is not None

    traceset_parameters['TARGET_SW'] = StringParameter(read_or_default(container.config, 'targetSW'))
    traceset_parameters['TARGET_HW'] = StringParameter(read_or_default(container.config, 'targetHW'))
    traceset_parameters['DATE'] = StringParameter(read_or_default(container.config, 'date'))

    # Try to read settings file and add additional parameters
    try:
        trace_folder = dirname(os.path.abspath(container.config.config.filename))
        extra_parameters = CWSettings.read(
            os.path.join(trace_folder, container.config.attr('prefix') + 'settings.cwset'))
        traceset_parameters.update(extra_parameters)
    except:
        print('Warning: Failed to read additional settings. Trace reading will continue without additional settings.')

    with TraceSet(path=output_path,
                  mode='w',
                  headers=headers,
                  padding_mode=TracePadding.AUTO) as trace_set:
        for n in range(0, len(container.traces)):
            trace_parameters = TraceParameterMap()
            if contains_textin:
                trace_parameters['INPUT'] = ByteArrayParameter(container.getTextin(n))
            if contains_textout:
                trace_parameters['OUTPUT'] = ByteArrayParameter(container.getTextout(n))
            if contains_keylist:
                trace_parameters['KEY'] = ByteArrayParameter(container.getKnownKey(n))
            trace_set.append(Trace(SampleCoding.FLOAT, container.getTrace(n), trace_parameters))


def read_or_default(config, attr: str, default: Any = ''):
    try:
        return config.attr(attr)
    except:
        return default


class CWSettings:
    @staticmethod
    def read(path: str) -> TraceSetParameterMap:
        parameters = TraceSetParameterMap()
        with open(path) as settings_file:
            lines = settings_file.readlines()
            category = ''
            for line in lines:
                line = line.strip()
                if line.startswith('['):
                    category = CWSettings.get_category(line, category)
                else:
                    matcher = re.search('(.*) = (.*)', line)
                    if matcher:
                        parameters[category + ":" + matcher.group(1)] = StringParameter(matcher.group(2))
        return parameters

    @staticmethod
    def get_category(line: str, category: str, level: int = 0) -> str:
        sub_category = line.replace('[', '').replace(']', '')
        if line.startswith('['):
            return CWSettings.get_category(line[1:], category, level + 1)
        else:
            if len(category.split(':')) >= level:
                category = ':'.join(category.split(':')[0:level - 1])
            if category == '':
                return sub_category
            else:
                return category + ':' + sub_category
