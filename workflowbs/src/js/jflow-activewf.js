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


	/* ActiveWF CLASS DEFINITION
	 * ========================= */

	var ActiveWF = function (element, options) {
		this.$element = $(element)
		this.options = $.extend({}, $.fn.activewf.defaults, options)
		if (this.options.serverURL == "") { this.options.serverURL = $.fn.activewf.defaults.serverURL; }
		this.reload()
	}

	ActiveWF.prototype.reload = function() {
		var $this = this,
			waiting_animation = ['<div class="container-fluid"><div class="row"><div class="col-md-1 col-md-offset-2"><div class="inline floatingBarsG">',
		                         '<div class="blockG" id="rotateG_01"></div>',
		                         '<div class="blockG" id="rotateG_02"></div>',
		                         '<div class="blockG" id="rotateG_03"></div>',
		                         '<div class="blockG" id="rotateG_04"></div>',
		                         '<div class="blockG" id="rotateG_05"></div>',
		                         '<div class="blockG" id="rotateG_06"></div>',
		                         '<div class="blockG" id="rotateG_07"></div>',
		                         '<div class="blockG" id="rotateG_08"></div>',
		                         '</div></div> <div class="col-md-8">Please wait until module is being loaded!</div></div></div>'].join('\n'),
		    url = this.options.serverURL + '/get_workflows_status?';
		if (this.options.metadataFilter.length > 0) {
			url += 'metadata_filter='+this.options.metadataFilter.join(',')+'&';
		}
		url += 'callback=?';
		$this.$element.html(waiting_animation);
		$.ajax({
		    url: url,
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
		    	var workflow_by_id = {},
		    		all_ids = new Array(),
		    		workflows_sorted = new Array();
		    	for (var i in data) { 
		    		workflow_by_id[data[i]["id"]] = data[i];
		    		all_ids.push(data[i]["id"]);
		    	}
		    	all_ids.sort(function(a, b) {
		    	    return b - a;
		    	});
		    	for (var i in all_ids) {
		    		workflows_sorted.push(workflow_by_id[all_ids[i]]);
		    	}
		    	$this.$element.html("");
		    	$.tmpl($this.options.template, {workflows: workflows_sorted}).appendTo($this.$element);
		    	$("[id^=activewf_btn_]").click(function(){
		    		var workflow_id = $(this).attr("id").split("activewf_btn_")[1];
		    		$this.$element.trigger('select.activewf', workflow_by_id[workflow_id]);
		    	});
		    	$("[id^=activewf_refresh_]").click(function(){
		    		$this.reload();
		    	});
		    	$("[id^=activewf_delete_]").click(function(){
		    		var workflow_id = $(this).attr("id").split("activewf_delete_")[1];
		    		$.ajax({
		    		    url: $this.options.serverURL + '/delete_workflow?workflow_id=' + workflow_id + '&callback=?',
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
		    	});
		    }
    	});
	}
	
	/* ActiveWF PLUGIN DEFINITION
	 * ========================== */
	
	var old = $.fn.activewf

	$.fn.activewf = function (option) {
		
		return this.each(function () {
			var $this = $(this)
				, data = $this.data('activewf')
				, options = $.extend({}, $.fn.activewf.defaults, typeof option == 'object' && option)
				, action = typeof option == 'string' ? option : null
			if (!data) $this.data('activewf', (data = new ActiveWF(this, options)))
			if (action) {  data[action]() }
		})
	}

	$.fn.activewf.defaults = {
		serverURL: "http://localhost:8080", 
		template: ['<table class="table table-striped table-striped">',
		    '<thead>',
		    '<tr>',
		    '<th>ID<th>',
			'<th>Name</th>',
			'<th>Status</th>',
			'<th>Start time</th>',
			'<th>End time</th>',
			'<th>Actions</th>',
		    '</tr>',
		    '</thead>',
		    '{{each(index, workflow) workflows}}',
		    '<tr>',
		    '<td><a id="activewf_btn_${workflow.id}" href="#">${workflow.id}</a><td>',
			'<td>${workflow.name}</td>',
		    '{{if workflow.status == "completed"}}',
		    '<td> <span class="label label-success">${workflow.status}</span></td>',
		    '{{else workflow.status == "failed"}}',
		    '<td> <span class="label label-danger">${workflow.status}</span></td>',
		    '{{else workflow.status == "aborted"}}',
		    '<td> <span class="label label-danger">${workflow.status}</span></td>',
		    '{{else workflow.status == "started"}}',
		    '<td> <span class="label label-info">${workflow.status}</span></td>',
		    '{{else workflow.status == "reseted"}}',
		    '<td> <span class="label label-default">${workflow.status}</span></td>',
		    '{{else}}',
			'<td>${workflow.status}</td>',
			'{{/if}}',
			'<td>${workflow.start_time}</td>',
			'<td>${workflow.end_time}</td>',
			'<td>',
			'  <div class="btn-group">',
			'    {{if workflow.status == "started"}}',
			'      <button type="button" id="activewf_refresh_${workflow.id}" class="btn btn-default btn-xs" aria-label="Left Align">',
			'    {{else}}',
			'      <button type="button" id="activewf_refresh_${workflow.id}" disabled class="btn btn-default btn-xs" aria-label="Left Align">',
			'    {{/if}}',
			'      <span class="glyphicon glyphicon-refresh"></span>',
			'    </button>',
			'    {{if workflow.status == "started"}}',
			'      <button type="button" id="activewf_delete_${workflow.id}" disabled class="btn btn-default btn-xs" aria-label="Left Align">',
			'    {{else}}',
			'      <button type="button" id="activewf_delete_${workflow.id}" class="btn btn-default btn-xs" aria-label="Left Align">',
			'    {{/if}}',
			'      <span class="glyphicon glyphicon-remove"></span>',
			'    </button>',
			'  </div>',
			'</td>',
			'</tr>',
			'{{/each}}',
			'</table>'].join('\n'),
		metadataFilter: []
	}

	$.fn.activewf.Constructor = ActiveWF

}(window.jQuery);  