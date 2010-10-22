/*  Authors:
 *    Pavel Zuna <pzuna@redhat.com>
 *    Endi S. Dewata <edewata@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; version 2 only
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

/* REQUIRES: ipa.js, details.js, search.js, add.js */

var ipa_entity_search_list = {};
var ipa_entity_add_list = {};

//moving this to details
//var ipa_entity_details_list = {};
var ipa_entity_association_list = {};

var ipa_entity_facet_list = {};

function ipa_facet(spec){
    return spec;
};


/* use this to track individual changes between two hashchange events */
var window_hash_cache = {};

function ipa_entity_set_search_definition(obj_name, data)
{
    ipa_entity_search_list[obj_name] = data;
}

function ipa_entity_set_add_definition(obj_name, data)
{
    ipa_entity_add_list[obj_name] = data;
}

function ipa_entity_set_details_definition(obj_name, data)
{
    ipa_entity_details_list[obj_name] = data;
}

function ipa_entity_get_details_sections(obj_name)
{
    var sections = ipa_entity_details_list[obj_name];
    if (sections) return sections;
    return [];
}

function ipa_entity_set_association_definition(obj_name, data)
{
    ipa_entity_association_list[obj_name] = data;
}


function ipa_entity_set_facet_definition(obj_name, data)
{
    function facet(spec){
        return spec;
    }

    ipa_entity_facet_list[obj_name] = data;
}


function ipa_details_only_setup(container){
    ipa_entity_setup(container, 'details');
}

function ipa_entity_setup(container, unspecified)
{

    var id = container.attr('id');
    var state = id + '-facet';
    var facet = $.bbq.getState(state, true) || unspecified || 'search';
    var last_facet = window_hash_cache[state];

    var facet_renders = {
        search : function(){
            state = id + '-filter';
            var filter = $.bbq.getState(state, true);
            var last_filter = window_hash_cache[state];
            if (filter == last_filter) return;
            _ipa_entity_setup(container);
            window_hash_cache[state] = filter;

        },
        details : function (){
            state = id + '-pkey';
            var pkey = $.bbq.getState(state, true);
            var last_pkey = window_hash_cache[state];
            if (pkey == last_pkey) return;
            _ipa_entity_setup(container);
            window_hash_cache[state] = pkey;
        },
        associate : function () {
            state = id + '-enroll';
            var enroll = $.bbq.getState(state, true);
            var last_enroll = window_hash_cache[state];
            if (enroll == last_enroll) return;
            _ipa_entity_setup(container);
            window_hash_cache[state] = enroll;
        },
        records : function () {
            state = id + '-record';
            var records = $.bbq.getState(state, true);
            var last_records = window_hash_cache[state];
            if (records == last_records) return;
            _ipa_entity_setup(container);
            window_hash_cache[state] = record;
        }
    };

    if (facet != last_facet) {
        _ipa_entity_setup(container,unspecified);
        window_hash_cache[state] = facet;
    } else{
        var render = facet_renders[facet];
        if (render) {
            render();
        }
        //TODO handle error.
    }

}

function _ipa_entity_setup(container, unspecified) {

    var obj_name = container.attr('id');

    function reset_on_click() {
        ipa_details_reset(container);
        return (false);
    }

    function update_on_click() {
        var pkey_name = ipa_objs[obj_name].primary_key;
        ipa_details_update(container, ipa_details_cache[obj_name][pkey_name][0]);
        return (false);
    }

    function new_on_click() {
        add_dialog_create(obj_name, ipa_entity_add_list[obj_name]);
        return (false);
    }

    function switch_view() {
        var enroll_obj_name = $(this).attr('title');
        var state = {};
        if (enroll_obj_name != 'search' &&
            enroll_obj_name != 'details' &&
            enroll_obj_name != 'records') {
            state[obj_name + '-facet'] = 'associate';
            state[obj_name + '-enroll'] = enroll_obj_name;
        } else {
            state[obj_name + '-facet'] = enroll_obj_name;
            state[obj_name + '-enroll'] = '';
        }
        $.bbq.pushState(state);
    }

    var facet_setups = {
        search : function (unspecified) {
            var filter = $.bbq.getState(obj_name + '-filter', true) || '';
            search_create(obj_name, ipa_entity_search_list[obj_name], container);
            ipa_make_button( 'ui-icon-plus',ipa_messages.button.add).
                click(new_on_click).
                appendTo($( "div#" + obj_name + " > div.search-controls"))
            search_load(container, filter);
        },

        details : function(unspecified) {
            var pkey = $.bbq.getState(obj_name + '-pkey', true);
            ipa_entity_generate_views(obj_name, container, switch_view);
            var sections = ipa_entity_get_details_sections(obj_name);
            ipa_details_create(container, sections);
            container.find('.details-reset').click(reset_on_click);
            container.find('.details-update').click(update_on_click);
            if (pkey||unspecified){
                ipa_details_load(container, pkey, null, null);
            }
        },

        associate : function facet(unspecified) {
            var pkey = $.bbq.getState(obj_name + '-pkey', true) || '';
            var enroll_obj_name = $.bbq.getState(obj_name + '-enroll', true) || '';
            var attr = ipa_get_member_attribute(obj_name, enroll_obj_name);
            var columns  = [
                {
                    title: ipa_objs[enroll_obj_name].label,
                    column: attr + '_' + enroll_obj_name
                }
            ];
            var association = ipa_entity_association_list[obj_name];
            var association_config = association ? association[enroll_obj_name] : null;
            var associator = association_config ? association_config.associator : null;
            var method = association_config ? association_config.method : null;
            var frm = new AssociationList(
                obj_name, pkey, enroll_obj_name, columns, container,
                associator, method
            );
            ipa_entity_generate_views(obj_name, container, switch_view);
            frm.setup();
        },

        records: function(unspecified) {
            records_facet.setup(obj_name, container, switch_view );
        }

    }


    container.empty();

    var facet = $.bbq.getState(obj_name + '-facet', true) ||
        unspecified || 'search';

    var facet_setup_function = facet_setups[facet];
    if (facet_setup_function){
        facet_setup_function(unspecified);
    }
}

function ipa_entity_generate_views(obj_name, container, switch_view)
{
    var ul = $('<ul></ul>', {'class': 'entity-views'});

    //TODO for single instance entites, don't display search
    ul.append($('<li></li>', {
        title: 'search',
        text: 'Search',
        click: switch_view
    }));

    ul.append($('<li></li>', {
        text: 'Details',
        title: 'details',
        click: switch_view
    }).prepend('| '));

    var attribute_members = ipa_objs[obj_name].attribute_members;
    for (attr in attribute_members) {
        var objs = attribute_members[attr];
        for (var i = 0; i < objs.length; ++i) {
            var m = objs[i];
            var label = ipa_objs[m].label;

            ul.append($('<li></li>', {
                title: m,
                text:label,
                click: switch_view
            }).prepend('| '));
        }
    }

    //TODO Additional facets go here

    var facets = ipa_entity_facet_list[obj_name];
    if (facets){
        for (var f = 0; f < facets.length; f += 1){
            var facet = facets[f];
            ul.append($('<li></li>', {
                text: facet.name,
                title: facet.name,
                click: switch_view
            }).prepend('| '));
        }
    }

    container.append(ul);
}

function ipa_entity_quick_links(tr, attr, value, entry_attrs) {

    var obj_name = tr.closest('.search-container').attr('title');
    var pkey = ipa_objs[obj_name].primary_key;
    var pkey_value = entry_attrs[pkey][0];

    var td = $("<td/>");
    tr.append(td);

    $("<a/>", {
        href: "#details",
        title: "Details",
        click: function() {
            var state = {};
            state[obj_name+'-facet'] = 'details';
            state[obj_name+'-pkey'] = pkey_value;
            nav_push_state(state);
            return false;
        }
    }).appendTo(td);

    var attribute_members = ipa_objs[obj_name].attribute_members;
    for (attr_name in attribute_members) {
        var objs = attribute_members[attr_name];
        for (var i = 0; i < objs.length; ++i) {
            var m = objs[i];
            var label = ipa_objs[m].label;

            $("<a/>", {
                href: '#'+m,
                title: label,
                text: label,
                click: function(m) {
                    return function() {
                        var state = {};
                        state[obj_name+'-facet'] = 'associate';
                        state[obj_name+'-enroll'] = m;
                        state[obj_name+'-pkey'] = pkey_value;
                        nav_push_state(state);
                        return false;
                    }
                }(m)
            }).append(' | ' ).appendTo(td);
        }
    }
}
