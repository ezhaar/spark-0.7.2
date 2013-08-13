#!/usr/bin/python


from subprocess import Popen, PIPE
import argparse
import re
import sys
import conf.defaults as defaults


def ssh(vm_ip, verbose=False):
    try:
        st = Popen(["ssh", "-l", "admin", "-i", "~/.ssh/id_rsa", vm_ip],
                   stdout=PIPE,
                   stderr=PIPE)
    except OSError as (errno, strerr):
        print("Could not login...\n User verbose for detailed error msg")
        if verbose:
            print(str(errno) + "\n" + str(strerr))

    return st


def scp(vm_ip, filename, spark_dir, verbose=False):

    try:
        dest = "admin@" + vm_ip + ":" + spark_dir
        print ("copying to " + dest)
        st = Popen(["scp", filename, dest],
                   stdout=PIPE,
                   stderr=PIPE)
    except OSError as (errno, strerr):
        print("Could not login...\n User verbose for detailed error msg")
        if verbose:
            print(str(errno) + "\n" + str(strerr))

    return st


def spawn_slaves(cluster_name, slave_template, num_slaves):

    slaves_list = {}

    print("Creating Slave Nodes...")
    try:
        for i in range(1, num_slaves + 1):
            # name the slave
            slave_name = "slave" + str(i) + "." + cluster_name
            result = Popen(["onetemplate", "instantiate",
                            slave_template, "--name", slave_name],
                           stdout=PIPE).communicate()[0]

            slave_id = result.strip('VM ID: ').strip('\n')
            vm_info = Popen(["onevm", "show", str(slave_id)],
                            stdout=PIPE).communicate()[0]
            ip_list = re.findall(r'[0-9]+(?:\.[0-9]+){3}', vm_info)

            slaves_list[slave_id] = ip_list[0]
        print(slaves_list)

    except:
        raise

    print("Done...")
    return slaves_list


def check_args(args):
    try:
        args.num_slaves = int(args.num_slaves)
        args.cluster_name = str(args.cluster_name)
        args.master_ip = str(args.master_ip)

        if args.num_slaves < 1:
            print("There are no slaves to create...")
            sys.exit(0)

        if args.num_slaves > 10:
            input = raw_input("Are you sure you want to create "
                              + args.num_slaves
                              + " Slaves? (y/n)")
            if input != 'y':
                print("OK, Give it another try")
                sys.exit(0)

        print("Cluster name will be set to: " + args.cluster_name)
        input = raw_input("To avoid HOSTNAME conflicts, Please verify that "
                          "cluster name is unique... Continue (y/n): ")
        if input == 'n':
            print("Ok, Exit...")
            sys.exit(0)

        if (args.master_ip).startswith("192"):
            print("I need a public IP address. Exit...")
            sys.exit(0)

        return args
    except:
        raise


def main():

    parser = argparse.ArgumentParser(description="Create a Spark Cluster on "
                                     "PDC Cloud.")
    parser.add_argument("-c", "--name", metavar="", dest="cluster_name",
                        action="store",
                        default=defaults.cluster_name,
                        help="Name for the cluster.")
    parser.add_argument("-n", "--num-slaves", metavar="", dest="num_slaves",
                        default=defaults.num_slaves,
                        type=int, action="store",
                        help="Number of slave nodes to spawn.")
    parser.add_argument("-m", "--master-ip", metavar="", dest="master_ip",
                        action="store", default=defaults.master_ip,
                        help="Ip address of Master")
    parser.add_argument("-v", "--verbose", metavar="", dest="verbose",
                        action="store", default=defaults.verbose,
                        help="verbose output")

    args = parser.parse_args()

    args = check_args(args)
    cluster_name = args.cluster_name
    num_slaves = args.num_slaves
    master_ip = args.master_ip
    verbose = args.verbose
    filename = defaults.filename
    slave_template = defaults.slave_template
    spark_dir = defaults.spark_dir

    slaves_dict = spawn_slaves(cluster_name, slave_template, num_slaves)
    slave_hostnames = []
    for slave_id, hostname in slaves_dict.items():
        print(hostname)
        slave_hostnames.append(str(hostname))
    slave_file = open(filename, "w")
    for host in slave_hostnames:
        slave_file.write(host + "\n")
    scp(master_ip, filename, spark_dir, verbose)


if __name__ == "__main__":
    main()
