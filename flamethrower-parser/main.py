import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import shlex
import glob

""" Get an argument for a command line string

:param cmd: the full flamethrower command
:param s: the argument to search for
:param default: the default value of this argument
:returns: The value of the argument, or the default value if the command is not found
"""
def get_argument(cmd, s, default):
    try:
        val = cmd[cmd.index(s) + 1]
    except ValueError:
        val = default
    return val

""" Prepare the pandas dataframe by reading and filtering it

:param filepath: the path to the file to read for reading
:returns: the pandas dataframe and the flamethrower command that was used
"""
def prepare_df(filepath):
    df = pd.read_json(filepath, lines=True)
    cmd = shlex.split(df.iloc[0, :]["cmdline"])
    df = df[pd.isna(df['total_response_avg_ms'])][1:]
    return df, cmd

""" Get a the round from the filepath

:param filepath: The filepath to get the round for
:returns: The round
"""
def get_round(filepath):
    rounds = ['round1', 'round2', 'round3', 'round4' ]
    return [x for x in rounds if x in filepath][0]

""" Get a the test from the filepath

:param filepath: The filepath to get the test for
:returns: The test 
"""
def get_test(filepath):
    tests = ['test1', 'test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8', 'test9' ]
    return [x for x in tests if x in filepath][0]

def get_resolver(cmd, resolvers):
    return [x for x in resolvers if x in cmd][0] 

""" Get the protocol by getting the argument and appending the HTTP method

:param cmd: the cmd to get the protocol f rom
:return: the protocol
"""
def get_protocol(cmd):
    protocol = get_argument(cmd, '-P', 'udp')
    if protocol == 'https':
        method = get_argument(cmd, '-M', 'GET')
        protocol += '-' + method
    return protocol


""" Parse the files by storing them in a dictionary

:param directory: the directories where the .json files are stored
:param subdir: The subdir to filter
:param plot_type: The type of plot to create
:param resolvers: The resolvers to get the data from
:returns: A dictionary of files
"""
def parse_files(directories, subdir, plot_type, resolvers):
    files = {}
    for directory in directories:
        for filepath in sorted(glob.glob(directory + '/**/*.json', recursive=True)):
            if '/' + subdir + '/' in filepath:
                df, cmd = prepare_df(filepath)
                concurrent_gens = int(get_argument(cmd, '-c', 10))
                protocol = get_protocol(cmd)
                record = df.to_records().reshape(-1, concurrent_gens)
                test = get_test(filepath)
                if plot_type == 'foreach':
                    current_round = get_round(filepath)
                    files[(protocol, test, current_round)] = [record]
                elif plot_type == 'resolver':
                    resolver = get_resolver(cmd, resolvers)
                    if (protocol, test, resolver) not in files:
                        files[(protocol, test, resolver)] = [record]
                    else:
                        files[(protocol, test, resolver)].append(record)
                else:
                    if (protocol, test) not in files:
                        files[(protocol, test)] = [record]
                    else:
                        files[(protocol, test)].append(record)
    return files

""" Get and merge data by doing an operation

:param files: The files to get data from
:param data_extractor: The function that extracts the data
:param post_extractor: Operation to do after extracting the data, default is the identity
:returns: The extracted values
"""
def get_data_and_merge(files, data_extractor, post_extractor=lambda x: x):
    extracted_values = {}
    extracted_latencies = []
    for key, values in files.items():
        val = data_extractor(values)
        if isinstance(val, np.ndarray) and val.size == 0:
            continue
        val = post_extractor(val)
        if len(key) > 2:
            current_key = (key[0], key[2])
        else:
            current_key = key[0]
        if current_key not in extracted_values:
            extracted_values[current_key] = [val]
        else:
            extracted_values[current_key].append(val)
    return extracted_values

""" Get the TCP latencies

:param: The values to get the TCP latencies from
:returns: TCP latencies
"""
def get_tcp_latencies(values):
    return np.concatenate([x.tcp_handshake[x.tcp_handshake != 0] for x in values]).ravel()

""" Get the TLS latencies

:param: The values to get the TLS latencies from
:returns: TLS latencies
"""
def get_tls_latencies(values):
    return np.concatenate([x.tls_handshake[x.tls_handshake != 0] for x in values]).ravel()

""" Get the round-trip times

:param: The values to get the RTT from
:returns: The RTTs
"""
def get_rtt(values):
    return np.concatenate([np.concatenate(list(filter(None, x.period_response_arr_ms.flatten()))) for x in values]).flatten()

""" Create a TCP latency plot

:param files: The files to create the plot for
:param plot_type: The type of plot
:param subdir: The subdir to use as filename
"""
def tcp_handshake_plot(files, plot_type, subdir):
    tcp_latencies = get_data_and_merge(files, get_tcp_latencies, np.mean)
    for key, values in tcp_latencies.items():
        filename_prefix = key
        if isinstance(key, tuple):
            filename_prefix = '-'.join(key)
        bar_plot(values, subdir + '-' + plot_type + '-' + filename_prefix + '-tcp-mean.png', "Tests as defined in Table 3.1", "TCP latency in milliseconds", 20)


""" Create a TLS latency plot

:param files: The files to create the plot for
:param plot_type: The type of plot
:param subdir: The subdir to use as filename
"""
def tls_handshake_plot(files, plot_type, subdir):
    tls_latencies = get_data_and_merge(files, get_tls_latencies, np.mean)
    for key, values in tls_latencies.items():
        filename_prefix = key
        if isinstance(key, tuple):
            filename_prefix = '-'.join(key)
        bar_plot(values, subdir + '-' + plot_type  + '-' + filename_prefix + '-tls-mean.png', "Tests as defined in Table 3.1", "TLS latency in milliseconds", 20)


""" Create a round-trip time plot

:param files: The files to create the plot for
:param plot_type: The type of plot
:param resolvers: The resolvers to filter
:param rounds: The rounds to get
:param subdir: The subdir to use as filename
"""
def rtt_mean_plot(files, plot_type, resolvers, rounds, subdir):
    rtt_mean = get_data_and_merge(files, get_rtt, np.mean)
    if plot_type == 'combined':
        three_bar_plot(rtt_mean['udp'], rtt_mean['https-GET'], rtt_mean['https-POST'], subdir + '-' + 'combined-rtt-mean.png', "Tests as defined in Table 3.1", "Round-trip time in milliseconds")
        difference_bar_plot(rtt_mean['udp'], rtt_mean['https-GET'], rtt_mean['https-POST'], subdir + '-' + 'combined-rtt-difference.png', "Tests as defined in Table 3.1", "Round-trip time difference (UDP) in milliseconds")
    elif plot_type == 'foreach':
        for _round in rounds:
            three_bar_plot(rtt_mean[('udp', _round)], rtt_mean[('https-GET', _round)], rtt_mean[('https-POST', _round)], subdir + '-' + _round + '-rtt-mean.png', "Tests as defined in Table 3.1", "Round-trip time in milliseconds")
            difference_bar_plot(rtt_mean[('udp', _round)], rtt_mean[('https-GET', _round)], rtt_mean[('https-POST', _round)], subdir + '-' + _round + '-rtt-difference.png', "Tests as defined in Table 3.1", "Round-trip time difference (UDP) in milliseconds")
    else:
        for resolver in resolvers:
            three_bar_plot(rtt_mean[('udp', resolver)], rtt_mean[('https-GET', resolver)], rtt_mean[('https-POST', resolver)], subdir + '-' + resolver + '-rtt-mean.png', "Tests as defined in Table 3.1", "Round-trip time in milliseconds")
            difference_bar_plot(rtt_mean[('udp', resolver)], rtt_mean[('https-GET', resolver)], rtt_mean[('https-POST', resolver)], subdir + '-' + resolver + '-rtt-difference.png', "Tests as defined in Table 3.1", "Round-trip difference (UDP) in milliseconds")

""" Create a round-trip time distribution plot

:param files: The files to create the plot for
:param plot_type: The type of plot
:param resolvers: The resolvers to filter
:param rounds: The rounds to get
:param subdir: The subdir to use as filename
"""
def rtt_cdf_plot(files, plot_type, resolvers, rounds, subdir):
    rtts = get_data_and_merge(files, get_rtt) 
    if plot_type == 'combined':
        for i in range(len(rtts['udp'])):
            cdf_plot(rtts['udp'][i], rtts['https-GET'][i], rtts['https-POST'][i], subdir + '-cdf-test' + str(i+1) + '.png', "Round-trip time in milliseconds", "Cumulative Probability")
    elif plot_type == 'resolver':
        for resolver in resolvers:
            for i in range(len(rtts[('udp', resolver)])):
                cdf_plot(rtts[('udp', resolver)][i], rtts[('https-GET', resolver)][i], rtts[('https-POST', resolver)][i], subdir + '-' + resolver + '-cdf-test' + str(i+1) + '.png', "Round-trip time in milliseconds", "Cumulative Probability")
    else:
        for _round in rounds:
            for i in range(len(rtts[('udp', _round)])):
                cdf_plot(rtts[('udp', _round)][i], rtts[('https-GET', _round)][i], rtts[('https-POST', _round)][i], subdir + '-' + _round + '-cdf-test' + str(i+1) + '.png', "Round-trip time in milliseconds", "Cumulative Probability")

""" Create a standard deviation round-trip time plot

:param files: The files to create the plot for
:param plot_type: The type of plot to create
:param resolvers: The resolvers to filter
:param rounds: The rounds to filter
:param subdir: The subdir to use as a filename prefix
"""
def rtt_stdev_plot(files, plot_type, resolvers, rounds, subdir):
    rtt_stdev = get_data_and_merge(files, get_rtt, np.std)
    if plot_type == 'combined':
        three_bar_plot(rtt_stdev['udp'], rtt_stdev['https-GET'], rtt_stdev['https-POST'], subdir + '-' + 'combined-rtt-stdev.png', "Tests as defined in Table 3.1", "Standard deviation in milliseconds")
    elif plot_type == 'foreach':
        for _round in rounds:
            three_bar_plot(rtt_stdev[('udp', _round)], rtt_stdev[('https-GET', _round)], rtt_stdev[('https-POST', _round)], subdir + '-' + _round + '-rtt-stdev.png', "Tests as defined in Table 3.1", "Standard deviation in milliseconds")
    else:
        for resolver in resolvers:
            three_bar_plot(rtt_stdev[('udp', resolver)], rtt_stdev[('https-GET', resolver)], rtt_stdev[('https-POST', resolver)], subdir + '-' + resolver + '-rtt-stdev.png', "Tests as defined in Table 3.1", "Standard deviation in milliseconds")

""" Three bar plot

:param array_udp: the UDP array to create the plot from
:param array_https_get: the HTTPS GET array to create the plot from
:param array_https_post: the HTTPS POST array to create the plot from
:param filename: the name of the file to save as
:param xlabel: The x-axis label
:param ylabel: The y-axis label
:param stepsize: the step size of the y axis, default=20
:param width: The width of the bars, default=5
"""
def three_bar_plot(array_udp, array_https_get, array_https_post, filename, xlabel, ylabel, stepsize=20, width=5):
    x_pos = np.arange(1, len(array_udp)+1)
    plt.figure()
    bbox = {'fc': '0.8', 'pad': 2}
    plt.rc('font', size=11)
    plt.rc('legend', fontsize=12)
    bars_udp = plt.bar((x_pos*width*4)-width, array_udp, width=width, color='blue', label="UDP", align='center')
    bars_https_get = plt.bar((x_pos*width*4), array_https_get, width=width, color='orange', label="HTTPS GET", align='center')
    bars_https_post = plt.bar((x_pos*width*4)+width, array_https_post, width=width, color='green', label="HTTPS POST", align='center')
    plt.xticks(x_pos*width*4, ["Test " + str(x) for x in x_pos])
    legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.savefig(filename, bbox_inches='tight')
    print("Saved {}".format(filename))

""" Simple bar plot

:param handshakes: the latency array to create the plot from
:param filename: the name of the file to save as
:param xlabel: The x-axis label
:param ylabel: The y-axis label
:param stepsize: the step size of the y axis, default=10
:param width: The width of the bars, default=5
"""
def bar_plot(handshakes, filename, xlabel, ylabel, stepsize=10, width=5):
    x_pos = np.arange(1, len(handshakes)+1)
    plt.figure()
    plt.rc('font', size=11)
    plt.rc('legend', fontsize=12)
    bars = plt.bar((x_pos*width*2), handshakes, width=width, color='blue', align='center')
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    for bar in bars:
        bar_height = bar.get_height()
        plt.text(bar.get_x()-width/4, bar_height+2, format(bar_height, '.2f'))

    plt.xticks(x_pos*width*2, ["Test " + str(x) for x in x_pos])
    y_ticks = np.arange(0, round(max(handshakes)+stepsize*2, -1), stepsize)
    plt.yticks(y_ticks)
    plt.savefig(filename)
    print("Saved {}".format(filename))


""" Three difference (HTTPS - UDP) bar plot

:param array_udp: the UDP array to create the plot from
:param array_https_get: the HTTPS GET array to create the plot from
:param array_https_post: the HTTPS POST array to create the plot from
:param filename: the name of the file to save as
:param xlabel: The x-axis label
:param ylabel: The y-axis label
:param stepsize: the step size of the y axis, default=20
:param width: The width of the bars, default=5
"""
def difference_bar_plot(array_udp, array_https_get, array_https_post, filename, xlabel, ylabel, stepsize=20, width=5):
    x_pos = np.arange(1, len(array_udp)+1)
    plt.figure()
    bbox = {'fc': '0.8', 'pad': 2}
    plt.rc('font', size=11)
    plt.rc('legend', fontsize=12)
    array_https_post_difference = np.subtract(np.asarray(array_https_post), np.asarray(array_udp))
    array_https_get_difference = np.subtract(np.asarray(array_https_get), np.asarray(array_udp))
    plt.axhline(y=0, color='black', linestyle='--')
    bars_https_get = plt.bar((x_pos*width*4), array_https_get_difference, width=width, color='orange', label="HTTPS GET", align='center')
    bars_https_post = plt.bar((x_pos*width*4)+width, array_https_post_difference, width=width, color='green', label="HTTPS POST", align='center')
    plt.xticks(x_pos*width*4, ["Test " + str(x) for x in x_pos])
    legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.savefig(filename, bbox_inches='tight')
    print("Saved {}".format(filename))

""" Create a cumulatitve distribution function plot

:param array_udp: the UDP array to create the plot from
:param array_https_get: the HTTPS GET array to create the plot from
:param array_https_post: the HTTPS POST array to create the plot from
:param filename: the name of the file to save as
:param xlabel: The x-axis label
:param ylabel: The y-axis label
"""
def cdf_plot(array_udp, array_https_get, array_https_post, filename, xlabel, ylabel):
    plt.figure()
    m = 2
    x_udp = np.sort(array_udp)
    y_udp = np.arange(1, len(x_udp)+1)/len(x_udp)
    x_https_get = np.sort(array_https_get)
    y_https_get = np.arange(1, len(x_https_get)+1)/len(x_https_get)
    x_https_post = np.sort(array_https_post)
    y_https_post = np.arange(1, len(x_https_post)+1)/len(x_https_post)
    
    plt.rc('font', size=14)
    plt.rc('legend', fontsize=14)
    plt.plot(x_https_post, y_https_post, marker='.',linestyle='none', color='green', label='HTTPS POST')
    plt.plot(x_https_get, y_https_get, marker='.', linestyle='none', color='orange', label='HTTPS GET')
    plt.plot(x_udp, y_udp, marker='.', linestyle='none', color='blue', label='UDP')
    if 'nocaching' in filename:
        plt.xlim(0, 1000)
    else:
        plt.xlim(0, 500)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend()
    plt.savefig(filename)
    print("Saved {}".format(filename))

""" The main function """
if __name__ == "__main__":
    plots = ['tcp_handshake', 'tls_handshake', 'rtt_mean', 'rtt_stdev', 'rtt_cdf']
    types = ['combined', 'foreach', 'resolver']
    resolvers = ['dns1.jwijenbergh.com', 'dns2.jwijenbergh.com']
    protocols = ['udp', 'https-GET', 'https-POST']
    rounds = ['round1', 'round2', 'round3', 'round4']
    subdir = 'nocaching'
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dirs', nargs='+', metavar='DIRS', help="A list of directories to use as input", required=True)
    parser.add_argument('-l', '--label', nargs='?', default='', metavar='LABEL', help="Prefix to use for the labels")
    parser.add_argument('-p', '--plots', nargs='+', choices=plots, help="Specify which plot(s) to create. Allowed values are: " + ', '.join(plots) + '. Default: rtt_mean_bar', default=['rtt_mean_bar'], metavar='TYPES')
    parser.add_argument('-t', '--type', nargs='?', choices=types, help="Specify how to parse the data. Allowed values are: " + ', '.join(types) + '. Default: combined', default='combined', metavar='PLOTS')
    parser.add_argument('-r', '--resolvers', nargs='+', help="Specify the resolvers to parse the query files for, used for 'server' ploot type", default=resolvers, metavar='RESOLVERS')
    args = parser.parse_args()
    files = parse_files(args.dirs, subdir, args.type, args.resolvers)
    if 'tcp_handshake' in args.plots:
        tcp_handshake_plot(files, args.type, subdir)
    if 'tls_handshake' in args.plots:
        tls_handshake_plot(files, args.type, subdir)
    if 'rtt_mean' in args.plots:
        rtt_mean_plot(files, args.type, resolvers, rounds, subdir)
    if 'rtt_cdf' in args.plots:
        rtt_cdf_plot(files, args.type, resolvers, rounds, subdir)
    if 'rtt_stdev' in args.plots:
        rtt_stdev_plot(files, args.type, resolvers, rounds, subdir)


