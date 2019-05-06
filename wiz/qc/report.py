#!/usr/bin/env python
# -*- coding: utf-8

"""
File that gathers the necessary functions to write report.
"""

import os
import time
import logging

from jinja2 import Environment
from jinja2 import FileSystemLoader

from wiz.qc import graphs

logger = logging.getLogger(__name__)


class Report:
    """
    Report object that contains the header object (report).
    and the object body (report)
    """
    def __init__(self, bins, args):
        self.header = Header(args)
        self.bins_data = [BinData(b, args) for b in bins]


class Header:
    """
    Object header that contains the parameters used to start wiz.
    """
    def __init__(self, args):
        self.date = time.asctime()
        self.input = args.genomes
        self.output = args.output
        self.window = args.window
        self.cpu = args.c
        # self.force = args.force
        self.finch = args.finchdb
        self.taxadb = args.taxadb


class BinData:
    """
    Bin object that retrieves data from a bin for writing the report.
    """
    def __init__(self, b, args):
        self.filename = b.filename
        self.path = b.path
        self.contigs = b.contigs
        self.window = args.window
        self.gc_map = graphs.scatter_gc(b.contigs, args.window)
        self.gc_density = graphs.distplot_gc(b.contigs)
        self.coding_density = graphs.scatter_gc_coding_density(b.contigs)
        self.tetra_heatmap = graphs.dendrogram_tetra(b.contigs, args.c)
        self.taxonomy_map = graphs.contigs_taxonomy(b.contigs)


def jinja_report(report_data, args):
    """
    Function that generates each sub report of the bins and
    the complete report before writing it to a file.
    """
    logger.info(" Make a wonderful report for you")
    bins_reports = jinja_bin_report(report_data.bins_data)
    complet_report = jinja_body(report_data.header, bins_reports)
    write_report(args, complet_report)


def jinja_bin_report(bins_data):
    """
    Function that generates a report for a bin.
    """
    file_loader = FileSystemLoader("wiz/misc/template", followlinks=True)
    env = Environment(loader=file_loader)
    sub_report = env.get_template("bin_report.html")
    bins_report = []
    for bin_data in bins_data:
        output = sub_report.render(
            bin_name=bin_data.filename,
            bin_path=bin_data.path,
            window=bin_data.window,
            contigs=bin_data.contigs,
            average_gc=bin_data.gc_map,
            gc_density=bin_data.gc_density,
            coding_density=bin_data.coding_density,
            tetra_heatmap=bin_data.tetra_heatmap,
            taxonomy_map=bin_data.taxonomy_map,
            )
        bins_report.append(output)
    return bins_report


def jinja_body(header_data, bins_reports):
    """
    Function that generates the full report.
    """
    file_loader = FileSystemLoader("wiz/misc/template", followlinks=True)
    env = Environment(loader=file_loader)
    template = env.get_template("report.html")
    output = template.render(
        date=header_data.date,
        inputs=header_data.input,
        output=header_data.output,
        window=header_data.window,
        cpu=header_data.cpu,
        taxadb=header_data.taxadb,
        sketchs=header_data.finch,
        profils=header_data.markers,
        bin_reports=bins_reports
    )
    return output


def write_report(args, report):
    """
    Function that writes the full report.
    """
    file_path = os.path.join(args.output, "QC_report.html")
    with open(file_path, "w") as report_file:
        report_file.writelines(report)
    logger.info(" The QC report has been successfully written")
