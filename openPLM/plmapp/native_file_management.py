from collections import defaultdict
native_to_standards = defaultdict(tuple)
native_to_standards.update(
    (
    (u'.fcstd', (u'.step', u'.stp')),
    (u'.catproduct', (u'.step', u'.stp')),
    (u'.catpart', (u'.step', u'.stp')),
))
