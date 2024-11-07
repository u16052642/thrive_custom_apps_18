/** @thrive-module **/
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";
const { Component, useSubEnv, useState, onMounted, onWillStart, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"

class ConstructionDashboard extends Component {
  setup() {
    this.rpc = useService("rpc");
    this.action = useService("action");
    this.orm = useService("orm");
    this.state = useState({
      constructionStats: {
        'con_sites': {},
        'total_site': 0,
        'total_project': 0,
        'total_mrq': 0,
        'job_sheet_count': 0,
        'job_order_count': 0,
        'project_planning': 0,
        'project_procurement': 0,
        'project_construction': 0,
        'project_handover': 0,
        'mr_draft': 0,
        'mr_waiting_approval': 0,
        'mr_approved': 0,
        'mr_ready_delivery': 0,
        'mr_material_arrive': 0,
        'mr_internal_transfer': 0,
        'back_order': 0,
        'it_draft': 0,
        'it_in_progress': 0,
        'it_done': 0,
        'forward_transfer': 0,
        'mr_po': 0,
        'equip_po': 0,
        'labour_po': 0,
        'overhead_po': 0,
      },
      constructionSite: {},
      constructionProjects: {},
    });
    useSubEnv({
      config: {
        ...getDefaultConfig(),
        ...this.env.config,
      },
    });
    this.siteTimeline = useRef('siteTimeline');
    this.siteStatus = useRef('siteStatus');
    this.projectStatus = useRef('projectStatus');
    this.projectTimeline = useRef('projectTimeline');
    this.materialRequisition = useRef('materialRequisition');
    this.internalTransfer = useRef('internalTransfer');
    this.purchaseOrder = useRef('purchaseOrder');
    onWillStart(async () => {
      await loadJS('/tk_construction_management/static/src/js/lib/moment.min.js');
      await loadJS('/tk_construction_management/static/src/js/lib/apexcharts.js');
      let constructionData = await this.orm.call('tk.construction.dashboard', 'get_construction_state', [false, false]);
      if (constructionData) {
        this.state.constructionStats = constructionData;
        this.state.constructionSite = constructionData['con_sites']
        this.state.siteTimelineRec = { 'site_data': constructionData['site_timeline'] };
        this.state.siteStatusRec = { 'count': constructionData['site_state'][1], 'site': constructionData['site_state'][0] };
        this.renderDashboardGraphData(constructionData);
      }
    });
    onMounted(() => {
      this.renderSiteTimeline();
      this.renderSiteStatus();
      this.renderDashboardGraph();
    })
  }
  renderDashboardGraph() {
    this.renderProjectStatus();
    this.renderProjectTimeline();
    this.renderMaterialRequisition();
    this.renderInternalTransfer();
    this.renderPurchaseOrder();
  }
  renderDashboardGraphData(constructionData) {
    this.state.projectStatusRec = { 'count': constructionData['project_status'][1], 'project': constructionData['project_status'][0] };
    this.state.projectTimelineRec = { 'project_timeline': constructionData['project_timeline'] };
    this.state.materialRequisitionRec = { 'count': constructionData['mrq_state'][1], 'mrq': constructionData['mrq_state'][0] };
    this.state.internalTransferRec = { 'count': constructionData['internal_state'][1], 'internal': constructionData['internal_state'][0] };
    this.state.purchaseOrderRec = {
      'jo': constructionData['job_order_po'][0],
      'material': constructionData['job_order_po'][1],
      'equip': constructionData['job_order_po'][2],
      'labour': constructionData['job_order_po'][3],
      'overhead': constructionData['job_order_po'][4]
    };
  }
  async getProjectList() {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let constructionSubProject = await this.orm.call('tk.construction.dashboard', 'get_project_list', [activeSite]);
    if (constructionSubProject) {
      this.state.constructionProjects = constructionSubProject
    }
    if (activeSite == 'all_site') {
      activeProject = 'all_project'
    }
    let constructionData = await this.orm.call('tk.construction.dashboard', 'get_construction_state', [activeSite, activeProject]);
    if (constructionData) {
      this.state.constructionStats = constructionData;
      this.renderDashboardGraphData(constructionData);
      this.renderDashboardGraph();
    }
  }
  async getProjectStates() {
    const activeSite = this.state.activeSite;
    const activeProject = this.state.activeProject;
    let constructionData = await this.orm.call('tk.construction.dashboard', 'get_construction_state', [activeSite, activeProject]);
    if (constructionData) {
      this.state.constructionStats = constructionData;
      this.renderDashboardGraphData(constructionData);
      this.renderDashboardGraph();
    }
  }
  // View Static
  async viewDashboardStatic(state, type) {
    let state_info;
    if (type == 'total') {
      state_info = await this.getTotalStatic(state)
    } else if (type == 'project') {
      state_info = await this.getProjectStatic(state)
    } else if (type == 'mrq') {
      state_info = await this.getMaterialState(state)
    } else if (type == 'internal') {
      state_info = await this.getInternalState(state)
    } else if (type == 'po') {
      state_info = await this.getPurchaseOrder(state)
    }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: state_info['name'],
      res_model: state_info['model'],
      view_mode: 'list',
      views: [[false, 'list'], [false, 'form']],
      target: 'current',
      context: { 'create': false },
      domain: state_info['domain'],
    });
  }
  async getTotalStatic(state) {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let domain = await this.orm.call('tk.construction.dashboard', 'get_construction_project_domain', [activeSite, activeProject]);
    let info = {};
    if (state == 'total_site') {
      info['model'] = 'tk.construction.site'
      info['name'] = 'Total Project'
      info['domain'] = []
    } else if (state == 'total_project') {
      info['model'] = 'tk.construction.project'
      info['name'] = 'Total Sub Project'
      info['domain'] = domain[0]
    } else if (state == 'total_mrq') {
      info['model'] = 'material.requisition'
      info['name'] = 'Material Requisition'
      info['domain'] = domain[1]
    } else if (state == 'total_job_sheet') {
      info['model'] = 'job.costing'
      info['name'] = 'Project Phase(WBS)'
      info['domain'] = domain[1]
    } else if (state == 'total_job_order') {
      info['model'] = 'job.order'
      info['name'] = 'Work Order'
      info['domain'] = domain[1]
    }
    return info
  }

  async getProjectStatic(state) {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let domain = ['stage', '=', state]
    let dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_construction_project_domain', [activeSite, activeProject]);
    dynamic_domain[0].push(domain)
    let info = {
      'model': 'tk.construction.project',
      'domain': dynamic_domain[0],
      'name': state
    }
    return info
  }
  async getMaterialState(state) {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let info = {};
    let domain = ['stage', '=', state];
    let dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_construction_project_domain', [activeSite, activeProject]);

    if (state == 'draft') {
      info['name'] = 'Draft'
      dynamic_domain[1].push(domain)
    } else if (state == 'department_approval') {
      info['name'] = 'Waiting Approvals'
      dynamic_domain[1].push(domain)
    } else if (state == 'approve') {
      info['name'] = 'In Progress'
      dynamic_domain[1].push(domain)
    } else if (state == 'ready_delivery') {
      info['name'] = 'Ready for Delivery'
      dynamic_domain[1].push(domain)
    } else if (state == 'material_arrived') {
      info['name'] = 'Material Arrived'
      dynamic_domain[1].push(domain)
    } else if (state == 'internal_transfer') {
      info['name'] = 'Internal Transfer'
      dynamic_domain[1].push(domain)
    } else if (state == 'back_order') {
      domain = ['is_back_order', '=', true]
      dynamic_domain[1].push(domain)
      info['name'] = 'Back Order'
    }
    info['domain'] = dynamic_domain[1]
    info['model'] = 'material.requisition'
    return info
  }
  async getInternalState(state) {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let info = {};
    let domain = ['stage', '=', state];
    let dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_construction_project_domain', [activeSite, activeProject]);
    if (state == 'draft') {
      info['name'] = 'Draft'
      dynamic_domain[0].push(domain)
    } else if (state == 'in_progress') {
      info['name'] = 'In Progress'
      dynamic_domain[0].push(domain)
    } else if (state == 'done') {
      info['name'] = 'Done'
      dynamic_domain[0].push(domain)
    } else if (state == 'is_forward_transfer') {
      domain = [state, '=', true]
      dynamic_domain[0].push(domain)
      info['name'] = 'Forward Transfer'
    }
    info['domain'] = dynamic_domain[1]
    info['model'] = 'internal.transfer'
    return info
  }
  async getPurchaseOrder(state) {
    let activeSite = this.state.activeSite;
    let activeProject = this.state.activeProject;
    let info = {};
    let dynamic_domain, domain;
    if (state == 'equip') {
      dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_job_order_po', [activeSite, activeProject, 'equip']);
      info['name'] = 'Equipment Purchase Order'
      info['model'] = 'purchase.order'
      info['domain'] = [['id', 'in', dynamic_domain]]
    } else if (state == 'labour') {
      dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_job_order_po', [activeSite, activeProject, 'labour']);
      info['name'] = 'Labour Purchase Order'
      info['model'] = 'purchase.order'
      info['domain'] = [['id', 'in', dynamic_domain]]
    } else if (state == 'overhead') {
      dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_job_order_po', [activeSite, activeProject, 'overhead']);
      info['name'] = 'Overhead Purchase Order'
      info['model'] = 'purchase.order'
      info['domain'] = [['id', 'in', dynamic_domain]]
    } else if (state == 'material') {
      domain = ['material_req_id', '!=', false];
      dynamic_domain = await this.orm.call('tk.construction.dashboard', 'get_construction_project_domain', [activeSite, activeProject]);
      dynamic_domain[1].push(domain)
      info['name'] = 'Material Purchase Order'
      info['model'] = 'purchase.order'
      info['domain'] = dynamic_domain[1]
    }
    return info
  }
  // Graph
  renderSiteTimeline() {
    let data = this.state.siteTimelineRec['site_data']
    let site_data = []
    for (const ss of data) {
      site_data.push({
        'name': ss['name'],
        'data': [{
          'x': 'Timeline',
          'y': [new Date(ss['start_date']).getTime(), new Date(ss['end_date']).getTime()]
        }]
      })
    }
    const options = {
      series: site_data,
      chart: {
        height: 350,
        type: 'rangeBar'
      },
      plotOptions: {
        bar: {
          horizontal: true
        }
      },
      dataLabels: {
        enabled: true,
        formatter: function (val) {
          var a = moment(val[0])
          var b = moment(val[1])
          var diff = b.diff(a, 'days')
          return diff + (diff > 1 ? ' days' : ' day')
        }
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'light',
          type: 'vertical',
          shadeIntensity: 0.25,
          gradientToColors: undefined,
          inverseColors: true,
          opacityFrom: 1,
          opacityTo: 1,
          stops: [50, 0, 100, 100]
        }
      },
      xaxis: {
        type: 'datetime'
      }
    };
    this.renderGraph(this.siteTimeline.el, options);
  }
  renderSiteStatus() {
    const options = {
      series: this.state.siteStatusRec['count'],
      chart: {
        type: 'donut',
        height: 410
      },
      colors: ['#95e2f9', '#f9aa4f', '#62dfc7'],
      dataLabels: {
        enabled: false
      },
      fill: {
        type: 'gradient',
      },
      labels: this.state.siteStatusRec['site'],
      legend: {
        position: 'bottom',
      },
    };
    this.renderGraph(this.siteStatus.el, options);
  }
  renderProjectStatus() {
    const options = {
      series: this.state.projectStatusRec['count'],
      chart: {
        type: 'donut',
        height: 410
      },
      dataLabels: {
        enabled: false
      },
      fill: {
        type: 'gradient',
      },
      labels: this.state.projectStatusRec['project'],
      legend: {
        position: 'bottom',
      },
    };
    $('#project_status').empty();
    this.renderGraph(this.projectStatus.el, options);
  }
  renderProjectTimeline() {
    let data = this.state.projectTimelineRec['project_timeline']
    let project_data = []
    for (const ss of data) {
      project_data.push({
        'name': ss['name'],
        'data': [{
          'x': "Project",
          'y': [new Date(ss['start_date']).getTime(), new Date(ss['end_date']).getTime()]
        }]
      })
    }
    const options = {
      series: project_data,
      chart: {
        height: 350,
        type: 'rangeBar'
      },
      plotOptions: {
        bar: {
          horizontal: true
        }
      },
      dataLabels: {
        enabled: true,
        formatter: function (val) {
          var a = moment(val[0])
          var b = moment(val[1])
          var diff = b.diff(a, 'days')
          return diff + (diff > 1 ? ' days' : ' day')
        }
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'light',
          type: 'vertical',
          shadeIntensity: 0.25,
          gradientToColors: undefined,
          inverseColors: true,
          opacityFrom: 1,
          opacityTo: 1,
          stops: [50, 0, 100, 100]
        }
      },
      xaxis: {
        type: 'datetime'
      }
    };
    $('#project_time_line').empty();
    this.renderGraph(this.projectTimeline.el, options);
  }
  renderMaterialRequisition() {
    const options = {
      series: this.state.materialRequisitionRec['count'],
      chart: {
        type: 'pie',
        height: 410
      },
      colors: ['#95e2f9', '#f9aa4f', '#efe7ac', '#9daacf', '#62dfc7', '#ff5765'],
      dataLabels: {
        enabled: false
      },
      labels: this.state.materialRequisitionRec['mrq'],
      legend: {
        position: 'bottom',
      },
    };
    $('#mrq_state').empty();
    this.renderGraph(this.materialRequisition.el, options);
  }
  renderInternalTransfer() {
    const options = {
      series: this.state.internalTransferRec['count'],
      chart: {
        type: 'donut',
        height: 410
      },
      colors: ['#95e2f9', '#f9aa4f', '#62dfc7'],
      dataLabels: {
        enabled: false
      },
      labels: this.state.internalTransferRec['internal'],
      legend: {
        position: 'bottom',
      },
    };
    $('#internal_transfer_state').empty();
    this.renderGraph(this.internalTransfer.el, options);
  }
  renderPurchaseOrder() {
    const options = {
      series: [
        {
          name: "Material Purchase Order",
          data: this.state.purchaseOrderRec['material']
        },
        {
          name: "Equipment Purchase Order",
          data: this.state.purchaseOrderRec['equip']
        },
        {
          name: "Labour Purchase Order",
          data: this.state.purchaseOrderRec['labour']
        },
        {
          name: "Overhead Purchase Order",
          data: this.state.purchaseOrderRec['overhead']
        }
      ],
      chart: {
        height: 350,
        type: 'line',
        zoom: {
          enabled: true
        },
      },
      dataLabels: {
        enabled: false
      },
      legend: {
        tooltipHoverFormatter: function (val, opts) {
          return val + ' - ' + opts.w.globals.series[opts.seriesIndex][opts.dataPointIndex] + ''
        }
      },
      markers: {
        size: 0,
        hover: {
          sizeOffset: 6
        }
      },
      xaxis: {
        categories: this.state.purchaseOrderRec['jo'],
      },
      tooltip: {
        y: [
          {
            title: {
              formatter: function (val) {
                return val + " Count"
              }
            }
          },
          {
            title: {
              formatter: function (val) {
                return val + " Count"
              }
            }
          }, {
            title: {
              formatter: function (val) {
                return val + " Count"
              }
            }
          }, {
            title: {
              formatter: function (val) {
                return val + " Count"
              }
            }
          },
          {
            title: {
              formatter: function (val) {
                return val;
              }
            }
          }
        ]
      },
      grid: {
        borderColor: '#f1f1f1',
      }
    };
    $('#job_order_po').empty();
    this.renderGraph(this.purchaseOrder.el, options);
  }
  renderGraph(el, options) {
    const graphData = new ApexCharts(el, options);
    graphData.render();
  }
}
ConstructionDashboard.template = "tk_construction_management.construction_dashboard";
registry.category("actions").add("construction_dash", ConstructionDashboard);