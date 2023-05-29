import json
import os
import xml.etree.ElementTree as ET
from typing import TypedDict, List, Literal
import re
import math

# Constants (Config)
MAX_CHAIN_NUMS = 1000
MAX_GRAPH_NUMS = 200
NEURON_NUM_STEP = 10
NEURON_GAP = 150
OUTPUT_DIR = 'output'
ONE_SPIKE_CHAIN_DIR = 'one-spike-chain'
ALL_SPIKE_CHAIN_DIR = 'all-spike-chain'
SIMPLE_COMPLETE_DIR = 'simple-complete'
BENCHMARK_COMPLETE_DIR = 'benchmark-complete'

class Position(TypedDict):
    x: float
    y: float

class Rule(TypedDict):
    language: str
    consume: int
    produce: int
    delay: int

class Neuron(TypedDict):
    id: str
    type: Literal['regular', 'input', 'output']
    position: Position
    rules: List[Rule]
    spikes: int

class Synapse(TypedDict):
    source: str
    target: str
    weight: float

class System(TypedDict):
    neurons: List[Neuron]
    synapses: List[Synapse]

def rule_to_v3_str(rule: Rule) -> str:
    consume = '' if rule['consume'] == 1 else f'^{rule["consume"]}'
    produce = '' if rule['produce'] == 1 else f'^{rule["produce"]}'
    return f'{rule["language"]}/a{consume}\\to a{produce};{rule["delay"]}'

def rule_to_v2_str(rule: Rule) -> str:
    language = re.sub(r'a\^(\d+)', r'\1a', rule['language']) \
        .replace('^', '').replace('\\ast', '*')
    consume = 'a' if rule['consume'] == 1 else f'{rule["consume"]}a'
    produce = 'a' if rule['produce'] == 1 else f'{rule["produce"]}a'
    return f'{language}/{consume}->{produce};{rule["delay"]}'

def export_to_json(data: System, path: str) -> None:
    with open(path, 'w') as file:
        system = {
            'neurons': [],
            'synapses': []
        }
        for neuron in data['neurons']:
            system['neurons'].append({
                'id': neuron['id'],
                'type': neuron['type'],
                'position': {
                    'x': neuron['position']['x'],
                    'y': neuron['position']['y']
                },
                'rules': list(map(rule_to_v3_str, neuron['rules'])),
                'content': neuron['spikes']
            })
        for synapse in data['synapses']:
            system['synapses'].append({
                'from': synapse['source'],
                'to': synapse['target'],
                'weight': synapse['weight']
            })

        json.dump(system, file, indent=4)

def export_to_xml(data: System, path: str) -> None:
    system = ET.Element('content')
    for neuron in data['neurons']:
        node = ET.SubElement(system, neuron['id'])

        id = ET.SubElement(node, 'id')
        id.text = neuron['id']

        position = ET.SubElement(node, 'position')
        x = ET.SubElement(position, 'x')
        x.text = str(neuron['position']['x'])
        y = ET.SubElement(position, 'y')
        y.text = str(neuron['position']['y'])

        rules = ET.SubElement(node, 'rules')
        rules.text = ' '.join(map(rule_to_v2_str, neuron['rules']))

        startingSpikes = ET.SubElement(node, 'startingSpikes')
        startingSpikes.text = str(neuron['spikes'])

        delay = ET.SubElement(node, 'delay')
        delay.text = '0'

        spikes = ET.SubElement(node, 'spikes')
        spikes.text = str(neuron['spikes'])

        isOutput = ET.SubElement(node, 'isOutput')
        isOutput.text = 'true' if neuron['type'] == 'output' else 'false'

        isInput = ET.SubElement(node, 'isInput')
        isInput.text = 'true' if neuron['type'] == 'input' else 'false'

        for synapse in data['synapses']:
            if synapse['source'] == neuron['id']:
                out = ET.SubElement(node, 'out')
                out.text = synapse['target']

        outWeights = ET.SubElement(node, 'outWeights')
        for synapse in data['synapses']:
            if synapse['source'] == neuron['id']:
                id = ET.SubElement(outWeights, synapse['target'])
                id.text = str(synapse['weight'])

    ET.ElementTree(system).write(path)

# Create chain systems (one spike and all spike)
system : System = {
    'neurons': [],
    'synapses': []
}
for neuron_num in range(0, MAX_CHAIN_NUMS + 1, NEURON_NUM_STEP):
    print(f'Creating spike chain system with {neuron_num + NEURON_NUM_STEP} neurons...')
    # Create neurons
    for i in range(NEURON_NUM_STEP):
        index = neuron_num + i
        system['neurons'].append({
            'id': f'N{index}',
            'type': 'regular',
            'position': {
                'x': index * NEURON_GAP,
                'y': 0
            },
            'rules': [{
                'language': 'a',
                'consume': 1,
                'produce': 1,
                'delay': 0
            }],
            'spikes': 1 if index == 0 else 0
        })

        # Create synapses
        if index > 0:
            system['synapses'].append({
                'source': f'N{index - 1}',
                'target': f'N{index}',
                'weight': 1
            })

    # One spike chain
    # Export to JSON
    export_to_json(system, os.path.join(
        f'{OUTPUT_DIR}/{ONE_SPIKE_CHAIN_DIR}/v3', 
        f'one-chain_{neuron_num + NEURON_NUM_STEP}.json')
    )
    # Export to XML
    export_to_xml(system, os.path.join(
        f'{OUTPUT_DIR}/{ONE_SPIKE_CHAIN_DIR}/v2',
        f'one-chain_{neuron_num + NEURON_NUM_STEP}.xmp')
    )

    # All spike chain
    for neuron in system['neurons'][neuron_num:neuron_num + NEURON_NUM_STEP]:
        neuron['spikes'] = 1
    # Export to JSON
    export_to_json(system, os.path.join(
        f'{OUTPUT_DIR}/{ALL_SPIKE_CHAIN_DIR}/v3',
        f'all-chain_{neuron_num + NEURON_NUM_STEP}.json')
    )
    # Export to XML
    export_to_xml(system, os.path.join(
        f'{OUTPUT_DIR}/{ALL_SPIKE_CHAIN_DIR}/v2',
        f'all-chain_{neuron_num + NEURON_NUM_STEP}.xmp')
    )

    # Clear spikes except N0
    for neuron in system['neurons'][1:]:
        neuron['spikes'] = 0

# Create simple complete graph
system : System = {
    'neurons': [],
    'synapses': []
}
for neuron_num in range(0, MAX_GRAPH_NUMS + 1, NEURON_NUM_STEP):
    print(f'Creating complete graph system with {neuron_num + NEURON_NUM_STEP} neurons...')
    radius = NEURON_GAP / 2 * (neuron_num + NEURON_NUM_STEP)

    for i in range(NEURON_NUM_STEP):
        # Create neuron
        index = neuron_num + i
        system['neurons'].append({
            'id': f'N{index}',
            'type': 'regular',
            'position': {
                'x': 0,
                'y': 0
            },
            'rules': [{
                'language': 'a^\\ast',
                'consume': 1,
                'produce': 1,
                'delay': 0
            }],
            'spikes': 1
        })

        # Create synapses
        for j in range(index):
            system['synapses'].append({
                'source': f'N{j}',
                'target': f'N{index}',
                'weight': 1
            })
            system['synapses'].append({
                'source': f'N{index}',
                'target': f'N{j}',
                'weight': 1
            })

    radius = (neuron_num + NEURON_NUM_STEP) * NEURON_GAP / 2
    for i in range(neuron_num + NEURON_NUM_STEP):
        theta = i * 2 * math.pi / (neuron_num + NEURON_NUM_STEP)
        system['neurons'][i]['position']['x'] = math.cos(theta) * radius
        system['neurons'][i]['position']['y'] = math.sin(theta) * radius

    # Simple graph
    # Export to JSON
    export_to_json(system, os.path.join(
        f'{OUTPUT_DIR}/{SIMPLE_COMPLETE_DIR}/v3',
        f'simple-complete_{neuron_num + NEURON_NUM_STEP}.json')
    )
    # Export to XML
    export_to_xml(system, os.path.join(
        f'{OUTPUT_DIR}/{SIMPLE_COMPLETE_DIR}/v2',
        f'simple-complete_{neuron_num + NEURON_NUM_STEP}.xmp')
    )

    # Set rules to be benchmark complete graphs
    for neuron in system['neurons']:
        neuron['rules'] = [{
                'language': '(a^2)^\\ast',
                'consume': 1,
                'produce': 1,
                'delay': 0
            }, {
                'language': '(a^2)^\\ast',
                'consume': 1,
                'produce': 2,
                'delay': 0
            }]
        neuron['spikes'] = 2
        
    # Export to JSON
    export_to_json(system, os.path.join(
        f'{OUTPUT_DIR}/{BENCHMARK_COMPLETE_DIR}/v3',
        f'benchmark-complete_{neuron_num + NEURON_NUM_STEP}.json')
    )
    # Export to XML
    export_to_xml(system, os.path.join(
        f'{OUTPUT_DIR}/{BENCHMARK_COMPLETE_DIR}/v2',
        f'benchmark-complete_{neuron_num + NEURON_NUM_STEP}.xmp')
    )

    # Return to simple
    for neuron in system['neurons']:
        neuron['rules'] = [{
                'language': 'a^\\ast',
                'consume': 1,
                'produce': 1,
                'delay': 0
            }]
        neuron['spikes'] = 1