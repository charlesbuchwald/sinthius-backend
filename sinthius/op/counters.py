#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:22
# ~

import time
import math
from sinthius.utils.dicttools import DotDict
from sinthius.errors import CounterError


class CounterManager(DotDict):
    def register(self, counter):
        name = counter.name
        if not name:
            raise CounterError('Cannot register counter with a blank name')
        existing = self.get(name, None)
        if existing:
            if isinstance(existing, DotDict):
                raise CounterError('Cannot register counter with name %s '
                                   'because a namespace with the same name '
                                   'was previously registered' % name)
            else:
                raise CounterError('Cannot register counter with name %s '
                                   'because a counter with the same name '
                                   'was previously registered' % name)
        try:
            self[name] = counter
        except KeyError:
            raise CounterError('Cannot register counter with name %s because a '
                               'portion of its namespace conflicts with a '
                               'previously registered counter' % name)


class BaseCounter(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def get_sampler(self):
        last_sample = [self._raw_sample()]

        def sampler_func():
            old_sample = last_sample[0]
            last_sample[0] = self._raw_sample()
            return self._computed_sample(old_sample, last_sample[0])

        return sampler_func

    def _raw_sample(self):
        raise NotImplementedError()

    def _computed_sample(self, one, two):
        raise NotImplementedError()


class TotalCounter(BaseCounter):
    def __init__(self, name, description):
        super(TotalCounter, self).__init__(name, description)
        self._counter = 0L

    def increment(self, value=1):
        self._counter += value

    def decrement(self, value=1):
        self._counter -= value

    def get_total(self):
        return self._counter

    def _raw_sample(self):
        return self._counter

    def _computed_sample(self, one, two):
        return two


class DeltaCounter(TotalCounter):
    def _computed_sample(self, one, two):
        return two - one


class RateCounter(TotalCounter):
    def __init__(self, name, description, unit_seconds=1, time_func=None):
        super(RateCounter, self).__init__(name, description)
        self._resolution = unit_seconds
        self._time_func = time_func or time.time

    def _raw_sample(self):
        return self._counter, self._time_func()

    def _computed_sample(self, one, two):
        time_diff = two[1] - one[1]
        if time_diff == 0:
            return 0
        return (two[0] - one[0]) * self._resolution / time_diff


class AverageCounter(BaseCounter):
    def __init__(self, name, description):
        super(AverageCounter, self).__init__(name, description)
        self._counter = 0L
        self._base_counter = 0L

    def add(self, value):
        self._counter += value
        self._base_counter += 1

    def _raw_sample(self):
        return self._counter, self._base_counter

    def _computed_sample(self, one, two):
        base_diff = two[1] - one[1]
        if base_diff == 0:
            return 0
        return (two[0] - one[0]) / base_diff


class Meter(object):
    """
    Example:
    --------
    .. code-block:: python
        from bs_core.op.counter import *

        counters = CounterManager()
        c_rate = RateCounter('module.rate', 'Rate Counter', 1)
        counters.register(c_rate)

        c_delta = DeltaCounter('module.delta', 'Delta Counter')
        counters.register(c_delta)

        meter = Meter()
        meter.add_counters(counters.module)

        sample = meter.sample()
        print sample.module.rate
        print sample.module.delta

        describe = meter.describe()
        print describe.module.rate
        print describe.module.delta
    """
    def __init__(self, counters=None):
        self._counters = {}
        self._description = None
        if counters is not None:
            self.add_counters(counters)

    def add_counters(self, counters):
        if isinstance(counters, DotDict):
            flat = counters.flatten()
            self._counters.update(
                [(value, value.get_sampler()) for value in flat.itervalues()])
        else:
            self._counters[counters] = counters.get_sampler()
        self._description = None

    def sample(self):
        sample = DotDict()
        for key in self._counters.keys():
            sample[key.name] = self._counters[key]()
        return sample

    def describe(self):
        if self._description is None:
            description = DotDict()
            for key in self._counters.keys():
                description[key.name] = key.description
            self._description = description
        return self._description


global_counters = CounterManager()


def define_total(name, description, manager=global_counters):
    counter = TotalCounter(name, description)
    manager.register(counter)
    return counter


def define_delta(name, description, manager=global_counters):
    counter = DeltaCounter(name, description)
    manager.register(counter)
    return counter


def define_rate(name, description, unit_seconds=1, manager=global_counters):
    counter = RateCounter(name, description, unit_seconds)
    manager.register(counter)
    return counter


def define_average(name, description, manager=global_counters):
    counter = AverageCounter(name, description)
    manager.register(counter)
    return counter


class RequestRateLimiter(object):
    """ rps: requests per second """

    def __init__(self, rps, unavailable_rps=0.0, rps_counter=None,
                 backoff_counter=None):
        self._rps = rps
        self._unavailable_rps = unavailable_rps
        self._rps_counter = rps_counter
        self._backoff_counter = backoff_counter
        self.available = self._rps - self._unavailable_rps
        self.last_time = time.time()

    def _rps(self):
        return self._rps - self._unavailable_rps

    def _recompute(self):
        now = time.time()
        delta = now - self.last_time
        limit = self._rps()
        self.available += limit * delta
        self.available = max(-limit, min(limit, self.available))
        self.last_time = now

    def add(self, requests):
        self.available -= requests
        if self._rps_counter is not None:
            self._rps_counter.increment(requests)

    def set_rps(self, rps):
        self.available += (rps - self._rps)
        self._rps = rps

    def set_unavailable_rps(self, unavailable_rps):
        self.available -= (unavailable_rps - self._unavailable_rps)
        self._unavailable_rps = unavailable_rps

    def compute_backoff_secs(self):
        self._recompute()
        if self.available >= 0.0:
            return 0.0
        else:
            backoff = min(1.0, math.fabs((self.available - 1.0) / self._rps()))
            if self._backoff_counter is not None:
                self._backoff_counter.increment(backoff)
            return backoff

    def needs_backoff(self):
        self._recompute()
        return self.available < 0.0
