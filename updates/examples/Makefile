################################################################################
# The Frenetic Project                                                         #
# frenetic@frenetic-lang.org                                                   #
################################################################################
# Licensed to the Frenetic Project by one or more contributors. See the        #
# NOTICE file distributed with this work for additional information            #
# regarding copyright and ownership. The Frenetic Project licenses this        #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################
# /updates/examples/Makefile                                                   #
# Examples Makefile                                                            #
################################################################################

NAIVE=main_naive
FLAVORS=1 2 3
OPTS=none subspace
TOPOLOGIES=FattreeTopology WaxmanTopology SmallWorldTopology
SMALLWORLD_SIZE=48
FATTREE_SIZE=32
WAXMAN_SIZE=48
RUN=../run.py

.PHONY: clean

examples: routing multicast

routing: fattree waxman smallworld

multicast: fattree_multicast waxman_multicast smallworld_multicast

smallworld:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "routing SmallWorldTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${SMALLWORLD_SIZE} smallworld $$flavor $$opt; \
	    done ; \
	done

fattree:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "routing FattreeTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${FATTREE_SIZE} fattree $$flavor $$opt; \
	    done ; \
	done

waxman:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "routing WaxmanTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${WAXMAN_SIZE} waxman $$flavor $$opt; \
		done ; \
	    done ; \
	done

smallworld_multicast:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "multicast SmallWorldTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${SMALLWORLD_SIZE} smallworld_multicast $$flavor $$opt; \
	    done ; \
	done

fattree_multicast:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "multicast FattreeTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${FATTREE_SIZE} fattree_multicast $$flavor $$opt; \
	    done ; \
	done

waxman_multicast:
	for flavor in ${FLAVORS}; do \
	    for opt in ${OPTS}; do \
		echo "multicast WaxmanTopology $${flavor} $${opt}"; \
		sudo ${RUN} -e -n ${WAXMAN_SIZE} waxman_multicast $$flavor $$opt; \
		done ; \
	    done ; \
	done