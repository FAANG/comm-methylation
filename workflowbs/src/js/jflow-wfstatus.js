/***************************************************************
*  Copyright notice
*
*  (c) 2015 PF bioinformatique de Toulouse
*  All rights reserved
* 
*  It is distributed under the terms of the GNU General Public 
*  License as published by the Free Software Foundation; either 
*  version 2 of the License, or (at your option) any later version.
*
*  The GNU General Public License can be found at
*  http://www.gnu.org/copyleft/gpl.html.
*
*  This script is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  This copyright notice MUST APPEAR in all copies of the script!
***************************************************************/

!function ($) {

	"use strict"; // jshint ;_;


	/* WFStatus CLASS DEFINITION
	 * ========================= */

	var WFStatus = function (element, options) {
		this.$element = $(element);
		this.options = $.extend({}, $.fn.wfstatus.defaults, options);
		this.cytoptions = {};
		if (this.options.serverURL == "") { this.options.serverURL = $.fn.activewf.defaults.serverURL; }
	}
	
	WFStatus.prototype.reformatWorkflowJSON = function(data) {
		var workflow = {
			name: data.name, 
			status: data.status,
			elapsed_time: data.elapsed_time,
			end_time: data.end_time,
			id: data.id,
			start_time: data.start_time,
			components: new Array()
	    };
		for (var i in data.components) {
    		var	failed    = 0,
    			completed = 0,
    			running   = 0,
    			waiting   = 0;
    		if(parseInt(data.components[i].total) != 0) {
    			failed    = parseInt(((parseInt(data.components[i].aborted) + parseInt(data.components[i].failed)) * 100) / parseInt(data.components[i].total)),
    			completed = parseInt((parseInt(data.components[i].completed) * 100) / parseInt(data.components[i].total)),
    			running   = parseInt((parseInt(data.components[i].running)   * 100) / parseInt(data.components[i].total)),
    			waiting   = parseInt((parseInt(data.components[i].waiting)   * 100) / parseInt(data.components[i].total));
    		}
    		workflow.components.push({
    			name: data.components[i].name,
    			elapsed_time: data.components[i].elapsed_time,
    			failed: failed,
    			running: running,
    			completed: completed,
    			waiting: waiting
    		});
    	}
		return workflow;
	}
	
	WFStatus.prototype._listview = function() {
		if (this.options.forceUsingWorkflow) {
			var workflow = this.reformatWorkflowJSON(this.options.forceUsingWorkflow);
			this.$element.html("");
			$.tmpl(this.options.headTemplate, {workflow: workflow, verbose:this.options.verbose}).appendTo(this.$element);
			$.tmpl(this.options.listTemplate, {workflow: workflow}).appendTo(this.$element);
			// force for first display, then reload an update
			this.options.forceUsingWorkflow = null;
		} else if (this.options.workflowID) {
			var $this = this,
				params = "",
				waiting_animation = ['<div class="container-fluid"><div class="row"><div class="col-md-1 col-md-offset-2"><div class="inline floatingBarsG">',
			                         '<div class="blockG" id="rotateG_01"></div>',
			                         '<div class="blockG" id="rotateG_02"></div>',
			                         '<div class="blockG" id="rotateG_03"></div>',
			                         '<div class="blockG" id="rotateG_04"></div>',
			                         '<div class="blockG" id="rotateG_05"></div>',
			                         '<div class="blockG" id="rotateG_06"></div>',
			                         '<div class="blockG" id="rotateG_07"></div>',
			                         '<div class="blockG" id="rotateG_08"></div>',
			                         '</div></div> <div class="col-md-8">Please wait until module is being loaded!</div></div></div>'].join('\n');
			$this.$element.html(waiting_animation);
			if (this.options.workflowID) { params = "workflow_id=" + this.options.workflowID + "&"; }
			params += "display=" + this.options.display + "&";
			$.ajax({
			    url: this.options.serverURL + '/get_workflow_status?'+params+'callback=?',
			    dataType: "json",
			    timeout: 20000,
			    error: function (xhr, ajaxOptions, thrownError) {
			    	var alert_message = ['<div class="alert alert-danger" role="alert">',
				        					'<strong>Error!</strong>',
				        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
				        					'</div>'].join('\n');
			        $this.$element.html(alert_message);
			    },
			    success: function(data) {
			    	var workflow = $this.reformatWorkflowJSON(data);
			    	$this.$element.html("");
			    	$.tmpl($this.options.headTemplate, {workflow: workflow, verbose:$this.options.verbose}).appendTo($this.$element);
			    	$.tmpl($this.options.listTemplate, {workflow: workflow}).appendTo($this.$element);
			    	
			    	// handle if there is some error
			    	$this.$element.find("#wfstatus_error_panel").hide();
			    	if( data.errors != null ) {
				    	$this.$element.find("#wfstatus_error_msg").html( data.errors["msg"].join('<br/>') );
				    	$this.$element.find("#wfstatus_error_location").text( data.errors["location"] );
				    	$this.$element.find("#wfstatus_error_panel").show();
			    	}
			    	
					$('[id^=progress_component_]').hover(function(){
						var rname = $(this).attr("id").split("progress_component_")[1],
							cname = rname.replace(".", "\\.");
						$("#reset_component_"+cname).children("div").css("left", $(this).width()-45);
						$("#info_component_"+cname).children("div").css("left", $(this).width()-89);
						$("#reset_component_"+cname).fadeIn(200);
						$("#info_component_"+cname).fadeIn(200);
						$("#reset_component_"+cname).bind("click", { component_name: rname, element: $this }, resetComponentHandler);
					}, function(){
						var cname = $(this).attr("id").split("progress_component_")[1].replace(".", "\\.");
						$("#reset_component_"+cname).fadeOut(200);
						$("#info_component_"+cname).fadeOut(200);
						$("#reset_component_"+cname).unbind("click", resetComponentHandler);
					});
			    }
	    	});
		}
	}
	
	WFStatus.prototype._createcytoscape = function(nodes, edges, $this) {
		
		var cytoptions = {
		  style: cytoscape.stylesheet()
		    .selector('node[type = "component"]')
		      .css({
		    	  'width': '80px',
		          'height': '80px',
		          'content': 'data(name)',
		          'pie-size': '100%',
		          'pie-1-background-color': 'lightgrey', //Error
		          'pie-1-background-size': 'mapData(err, 0, 100, 0, 100)',
		          'pie-2-background-color': '#faa732',   //Waiting
		          'pie-2-background-size': 'mapData(wai, 0, 100, 0, 100)',
		          'pie-3-background-color': '#0e90d2',   //Running
		          'pie-3-background-size': 'mapData(run, 0, 100, 0, 100)',
		          'pie-4-background-color': '#dd514c',   //Failed
		          'pie-4-background-size': 'mapData(fai, 0, 100, 0, 100)',
		          'pie-5-background-color': '#7fe175',   //Completed
		          'pie-5-background-size': 'mapData(com, 0, 100, 0, 100)',
		          'background-color': 'lightgrey',
		          'text-valign': 'bottom',
		          'color': 'black',
		          'font-family': '"Trebuchet MS",Verdana,"Lucida Grande", Tahoma, Helvetica, sans-serif',
		          'border-width' : '0', 
		          'font-size': '10px'
		      })
		    .selector('node[type ^= "input"]')
		      .css({
		    	  'width': '62px',
		          'height': '62px',
		    	  'content': 'data(name)',
		    	  'text-valign': 'bottom',
		          'color': 'black',
		          'font-family': '"Trebuchet MS",Verdana,"Lucida Grande", Tahoma, Helvetica, sans-serif',
		          'font-size': '10px',
		          'border-width' : '0'
		      })
		    .selector('edge')
		      .css({
		    	  'width': 1,
		          'opacity': 0.5
		      }),
  		elements: {
  		  nodes: nodes,
  		  edges: edges
		  },
		  layout: {
			  name: 'dagre',

			  // dagre algo options, uses default value on undefined
			  nodeSep: undefined, // the separation between adjacent nodes in the same rank
			  edgeSep: undefined, // the separation between adjacent edges in the same rank
			  rankSep: undefined, // the separation between adjacent nodes in the same rank
			  rankDir: 'LR', // 'TB' for top to bottom flow, 'LR' for left to right
			  minLen: function( edge ){ return 1; }, // number of ranks to keep between the source and target of the edge
			  
			  // general layout options
			  fit: true, // whether to fit to viewport
			  padding: 30, // fit padding
			  animate: false, // whether to transition the node positions
			  animationDuration: 500, // duration of animation in ms if enabled
			  boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
			  ready: function(){}, // on layoutready
			  stop: function(){} // on layoutstop
		  },
		  ready: function(){
		    window.cy = this;

		    cy.elements().unselectify();
		    cy.on('mouseover', 'node', function(e){
		    	var node = e.cyTarget;
		    	if(node._private.data.type == 'component') {
		    		node.animate({css: {'background-opacity':'0.1'} }, {duration: 100});
		    	}
		    	else {
		    		node.animate({css: {'background-opacity':'0.7'} }, {duration: 100});
		    	}
		    });
		    cy.on('mouseout', 'node', function(e){
		    	var node = e.cyTarget;
		    	if(node._private.data.type == 'button') {
		    		node.animate({css: {'background-opacity':'0.8'} }, {duration: 100});
		    	}
		    	else {
		    		node.animate({css: {'background-opacity':'1'} }, {duration: 100});
		    	}
		    });
		    cy.on('tap', 'node', function(e){
		      var node = e.cyTarget; 
		    
		      if(node.id() == 'reset') {
		    	  $this.reset(node._private.data.cname);
		      }
		      else if(node.id() == 'info') {
		    	  //$this.info(node._private.data.cname);
		      }
		      else if(node._private.data.type == 'component'){
		    	  if(cy.$("node[id = 'reset']").inside()) {
		    		  cy.remove("node[type = 'button']");
		    		  cy.elements().unlock();
		    	  }
		    	  else {
	    		      cy.add(
	    		       		{ group: "nodes",
	    		       	      data: { id: "reset", name: "", cname: node.id(), type: "button" },
	    		       	      css: {
	    		    	    	  'width':  '0px',
	    		    	          'height': '0px',
	    		    	          'background-color': 'black',
	    		    	          'background-opacity' : '0.8',
	    		    	          'content': 'data(name)',
	    		    	          'shape': 'roundrectangle'
	    		    		  },
	    		        	  position: { x: (node.position().x +21), y: (node.position().y -47) }
	    		    		}
	    		      ).animate({css: {'width': 20, 'height': 15}}, {duration: 150});
	    		      /* info button
	    		      cy.add(
	    		       		{ group: "nodes",
		    		       	  data: { id: "info", name: "", cname: node.id(), type: "button" },
		    		       	  css: {
	    		    	    	  'width':  '0px',
	    		    	          'height': '0px',
	    		    	          'border-width': '0px',
	    		    	          'background-color': 'black',
	    		    	          'background-opacity' : '0.8',
	    		    	          'content': 'data(name)',
	    		    	          'shape': 'roundrectangle'
		    		    	  },
		    		          position: { x: (node.position().x -11), y: (node.position().y -53) }
		    		       	}
	    		      ).animate({css: {'width': 20, 'height': 15}}, {duration: 150});
	    		      */
	    		      cy.$("node[type = 'button']").lock();
	    		      node.lock();
  		      }
  		   }
		    });
		    cy.on('tap', function(e){
	    	  if( e.cyTarget === cy ){
		        //cy.elements().removeClass('faded');
		      }
		    });
		    cy.boxSelectionEnabled(false);
		    cy.panzoom({});
		  }
		}
		$this.cytoptions = cytoptions;
		$('#cytoscape_panel').cytoscape(cytoptions);
	}
	
	WFStatus.prototype.render = function() {
		// handle a bootstrap bug in case the status is in a modal
		$(document).off('focusin.bs.modal');
		$('#cytoscape_panel').cytoscape(this.cytoptions);
	}
	
	WFStatus.prototype._graphview = function() {
		var $this = this,
			params = "",
			waiting_animation = ['<div class="container-fluid"><div class="row"><div class="col-md-1 col-md-offset-2"><div class="inline floatingBarsG">',
		                         '<div class="blockG" id="rotateG_01"></div>',
		                         '<div class="blockG" id="rotateG_02"></div>',
		                         '<div class="blockG" id="rotateG_03"></div>',
		                         '<div class="blockG" id="rotateG_04"></div>',
		                         '<div class="blockG" id="rotateG_05"></div>',
		                         '<div class="blockG" id="rotateG_06"></div>',
		                         '<div class="blockG" id="rotateG_07"></div>',
		                         '<div class="blockG" id="rotateG_08"></div>',
		                         '</div></div> <div class="col-md-8">Please wait until modul is being loaded!</div></div></div>'].join('\n');
		$this.$element.html(waiting_animation);
		if (this.options.workflowID) { params = "workflow_id=" + this.options.workflowID + "&"; }
		params += "display=" + this.options.display + "&";
		$.ajax({
		    url: this.options.serverURL + '/get_workflow_status?'+params+'callback=?',
		    dataType: "json",
		    timeout: 20000,
		    error: function (xhr, ajaxOptions, thrownError) {
		    	var alert_message = ['<div class="alert alert-danger" role="alert">',
			        					'<strong>Error!</strong>',
			        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
			        					'</div>'].join('\n');
		        $this.$element.html(alert_message);
		    },
		    success: function(data) {
		    	var workflow = $this.reformatWorkflowJSON(data);
			    $this.$element.html("");
			    $.tmpl($this.options.headTemplate, {workflow: workflow, verbose:$this.options.verbose}).appendTo($this.$element);
			    $.tmpl($this.options.graphTemplate, {workflow: workflow}).appendTo($this.$element);

		    	// prepare the data
		    	var	components = {},
		    		nodes = new Array(),
		    		edges = new Array();
		    	for (var i in data.components) {
		    		var err = 0,
		    		wai = workflow.components[i].waiting,
		    		run = workflow.components[i].running,
		    		fai = workflow.components[i].failed,
		    		com = workflow.components[i].completed;
		    		if((wai+run+fai+com)==0) { err = 100; }
		    		components[data.components[i].name] = { 
		    			name: data.components[i].name,
		    			err:  err,
		    			wai:  wai,
		    			run:  run,
		    			fai:  fai,
		    			com:  com 
		    		}
		    	}
		    	for (var i in data.nodes) {
		    		if(data.nodes[i].type == "inputfile" || data.nodes[i].type == "inputfiles" || data.nodes[i].type == "inputdirectory") {
		    			nodes.push({ data: {
		    				id:   data.nodes[i].name,
			    			name: data.nodes[i].display_name,
			    			type: data.nodes[i].type }
		    			});
		    		}
		    		else if(data.nodes[i].type == "component") {
		    			nodes.push({ data: {
		    				id:   data.nodes[i].name,
			    			name: data.nodes[i].display_name,
			    			type: data.nodes[i].type,
			    			err:  components[data.nodes[i].name].err,
			    			wai:  components[data.nodes[i].name].wai,
			    			run:  components[data.nodes[i].name].run,
			    			fai:  components[data.nodes[i].name].fai,
			    			com:  components[data.nodes[i].name].com }
		    			});
		    		}
		    	}
		    	for (var i in data.edges) {
		    		if (data.edges[i][0] != null && data.edges[i][1] != null) {
		    			edges.push({ data: { source: data.edges[i][0], target: data.edges[i][1] } });
		    		}
		    	}

		    	// handle if there is some errors
		    	$this.$element.find("#wfstatus_error_panel").hide();
		    	if( data.errors != null ) {
			    	$this.$element.find("#wfstatus_error_msg").html( data.errors["msg"].join('<br/>') );
			    	$this.$element.find("#wfstatus_error_location").text( data.errors["location"] );
			    	$this.$element.find("#wfstatus_error_panel").show();
		    	}
		    	$this._createcytoscape(nodes, edges, $this);
		    }
    	});
	}
	
	WFStatus.prototype.reload = function() {
		if (this.options.display == "list") {
			this._listview();
		} else if (this.options.display == "graph") {
			this._graphview();
		}
	}
	
	WFStatus.prototype.rerun = function() {
		var $this = this;
		$.ajax({
		    url: this.options.serverURL + '/rerun_workflow?workflow_id='+$this.options.workflowID+'&callback=?',
		    dataType: "json",
		    timeout: 20000,
		    error: function (xhr, ajaxOptions, thrownError) {
		    	var alert_message = ['<div class="alert alert-danger" role="alert">',
			        					'<strong>Error!</strong>',
			        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
			        					'</div>'].join('\n');
		        $this.$element.html(alert_message);
		    },
		    success: function(data) {
		    	$this.reload();
		    }
		});
	}
	
	var resetComponentHandler = function(event) { event.data.element.reset(event.data.component_name); }
	
	WFStatus.prototype.reset = function(component_name) {
		var $this = this,
			params = "";
		
		if (this.options.workflowID) { params = "workflow_id=" + this.options.workflowID + "&"; }
		params += 'component_name='+component_name+'&';
		
		$.ajax({
		    url: this.options.serverURL + '/reset_workflow_component?'+params+'&callback=?',
		    dataType: "json",
		    timeout: 20000,
		    error: function (xhr, ajaxOptions, thrownError) {
		    	var alert_message = ['<div class="alert alert-danger" role="alert">',
			        					'<strong>Error!</strong>',
			        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
			        					'</div>'].join('\n');
		        $this.$element.html(alert_message);
		    },
		    success: function(data) {
		    	$this.reload();
		    }
		});	
	}
	
	/* WFStatus PLUGIN DEFINITION
	 * ========================== */
	
	var old = $.fn.wfstatus

	$.fn.wfstatus = function (option) {
		return this.each(function () {
			var $this = $(this)
				, data = $this.data('wfstatus')
				, options = $.extend({}, $.fn.wfstatus.defaults, typeof option == 'object' && option)
				, action = typeof option == 'string' ? option : null
			// if already exist
			if (!data) $this.data('wfstatus', (data = new WFStatus(this, options)))
			// otherwise change the workflow
			else if (options.workflowID) { data.options.workflowID = options.workflowID; }
			if (options.forceUsingWorkflow) { data.options.forceUsingWorkflow = options.forceUsingWorkflow; }
			if (action) { data[action]() }
			else { data.reload(); }
		})
	}
	
	$.fn.wfstatus.defaults = {
		serverURL: "http://localhost:8080",
		headTemplate: ['<dl class="dl-horizontal">',
		   		    '<dt>Start</dt>',
				    '<dd>${workflow.start_time}</dd>',
				    '<dt>End</dt>',
				    '<dd>${workflow.end_time}</dd>',
			        '<dt>Elapsed time</dt>',
				    '<dd>${workflow.elapsed_time}</dd>',
				    '</dl>',
				    '<div id="wfstatus_error_panel" class="alert alert-danger" role="alert" style="display:none;">',
				    '    <strong>Error!</strong>',
				    '    <span id="wfstatus_error_msg"></span><br/>',
				    '    {{if verbose}}',
				    '      <strong>Error location:</strong><br/>',
				    '      <span id="wfstatus_error_location"></span>',
				    '    {{/if}}',
				    '</div>'].join('\n'),
		listTemplate: ['<dl class="dl-horizontal">',
		    '{{each(index, component) workflow.components}}',
		    '<dt>${component.name}</dt>',
		    '<dd>',
		    '<div id="progress_component_${component.name}" class="progress">',
		    '  <div class="progress-bar progress-bar-success" role="progressbar" style="width:${component.completed}%;"></div>',
		    '  <div class="progress-bar progress-bar-danger" role="progressbar" style="width:${component.failed}%;"></div>',
		    '  <div class="progress-bar progress-bar-info" role="progressbar" style="width:${component.running}%;"></div>',
		    '  <div class="progress-bar progress-bar-warning" role="progressbar" style="width:${component.waiting}%;"></div>',
		    '  <div id="reset_component_${component.name}" class="tooltip in" style="position:absolute;cursor:pointer;display:none;">',
		    '    <div class="tooltip-inner" style="position:absolute;top:-5px;height:29px;padding-top:4px;"><span style="font-size:20px;" class="glyphicon glyphicon-remove"></span></div>',
		    '  </div>',
//		    '  <div id="info_component_${component.name}" class="tooltip in" style="position:absolute; cursor: pointer; display: none;">',
//		    '    <div class="tooltip-inner" style="position:absolute; top:-5px"><span style="font-size: 20px;" class="glyphicon glyphicon-info-sign"></span></div>',
//		    '  </div>',
		    '</div>',
		    '</dd>',
		    '{{/each}}',
		    '</dl>'].join('\n'),
		graphTemplate: ['<div id="cytoscape_panel" style="background-image:url(img/grid.png);',
		    'background-color:#f9f9f9;margin-top:20px;border:1px solid lightgrey;border-radius:5px;',
		    'width:870px;height:393px">',
		    '</div>'].join('\n'),
		workflowID: null,
		forceUsingWorkflow: null,
		verbose: false,
		display: "graph"
	}

	$.fn.wfstatus.Constructor = WFStatus

}(window.jQuery);  