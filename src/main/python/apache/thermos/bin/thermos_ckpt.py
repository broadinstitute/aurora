#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

import pprint
import sys
import time

from twitter.common import app
from twitter.common.recordio import RecordIO, ThriftRecordReader

from apache.thermos.common.ckpt import CheckpointDispatcher

from gen.apache.thermos.ttypes import RunnerCkpt, RunnerState, TaskState

app.add_option(
    "--checkpoint",
    dest="ckpt",
    metavar="CKPT",
    help="read checkpoint from CKPT")

app.add_option(
    "--assemble",
    dest="assemble",
    metavar="CKPT",
    default=True,
    help="whether or not to replay the checkpoint records.")


def main(args):
  values = app.get_options()

  if len(args) > 0:
    print("ERROR: unrecognized arguments: %s\n" % (" ".join(args)), file=sys.stderr)
    app.help()
    sys.exit(1)

  if not values.ckpt:
    print("ERROR: must supply --checkpoint", file=sys.stderr)
    app.help()
    sys.exit(1)

  fp = file(values.ckpt, "r")
  rr = ThriftRecordReader(fp, RunnerCkpt)
  wrs = RunnerState(processes={})
  dispatcher = CheckpointDispatcher()
  try:
    for wts in rr:
      print('Recovering: %s' % wts)
      if values.assemble is True:
        dispatcher.dispatch(wrs, wts)
  except RecordIO.Error as err:
    print('Error recovering checkpoint stream: %s' % err, file=sys.stderr)
    return
  print('\n\n\n')
  if values.assemble:
    print('Recovered Task Header')
    pprint.pprint(wrs.header, indent=4)

    print('\nRecovered Task States')
    for task_status in wrs.statuses:
      print('  %s [pid: %d] => %s' % (
          time.asctime(time.localtime(task_status.timestamp_ms / 1000.0)),
          task_status.runner_pid,
          TaskState._VALUES_TO_NAMES[task_status.state]))

    print('\nRecovered Processes')
    pprint.pprint(wrs.processes, indent=4)


app.main()
