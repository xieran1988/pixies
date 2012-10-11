
function show_index() {
	var cats = ['substr', 'subip', 'baidu', 'taobao', 'sohu', 'zol', 'job51'];
	var l = [];
	var html = '';
	for (i in cats) {
		l.push(cats[i]);
		if (l.length == 3 || i == cats.length - 1) {
			html += '<div class=row-fluid>';
			for (j in l) {
				cat = l[j];
				html += '<div class="span4 index-span4">';
				html += template('index_' + cat, {});
				href = '?add,' + cat;
				html += '<p><a href=' + href + '><button class="btn">添加</button></a></p>';
				html += '</div>';
			}
			html += '</div>'
				l = [];
		}
	}
	$('#main_div').html(template('index_html', {html:html}));
}

hostlist = ['test.org', 'aaaa.com.cn', '192.168.1.1'];

function get_all_field_in() {
	var a = {};
	var fi = $('[field_in]');
	fi.each(function() {
		k = $(this).attr('field_in');
		v = this.value;
		a[k] = v;
	});
	fi = $('[field_in_2]');
	if (fi.length) {
		a['in_2'] = [];
		for (i = 0; i < fi.length; i += 2) {
			a['in_2'].push([fi[i].value, fi[i+1].value]);
		}
	}
	fi = $('[field_in_n]');
	if (fi.length) {
		a['in_n'] = [];
		for (i = 0; i < fi.length; i += 1) {
			a['in_n'].push(fi[i].value);
		}
	}
	fi = $('input[type=radio]:checked,textarea');
	fi.each(function() {
		a[$(this).attr('name')] = this.value;
	});
	a.cat = qa[1];
	if (qa[2]) {
		a.id = qa[2];
	}
	return JSON.stringify(a);
}

function edit_has_field_empty() {
	var has_empty = 0;
	$('.form-errmsg').html('');

	$('[field_in],[field_in_2],[field_in_n]').each(function() {
		var empty;
		if ($(this).is('select')) {
			empty = ($(this).attr('value') == '请选择');
		} else {
			empty = ($(this).val() == '');
		}
		if (empty) {
			msg = '注意：字段不能为空！';
			if ($(this).attr('field_in') == 'upload_img_path') {
				msg = '注意：请选择上传图片！'
			}
			$(this).parent().find('.form-errmsg').html(msg);
			has_empty = 1;
		}
	});

	$('#form_btn_tips').html('');
	if (has_empty) {
		$('#form_btn_tips').html('<font color=red>注意：请完整填写选项！</font>');
	}

	return has_empty;
}

function edit_form_ok(e) {
	e.preventDefault();

	if (!edit_has_field_empty()) {
		$('#form_btn_tips').html('保存中，请稍后 ...');
		$(e.target).addClass('disabled');

		var s = get_all_field_in();
		$.post('getinfo.py?' + qa[0], s, function(d) {
			$('#form_btn_tips').html('');
			$(e.target).removeClass('disabled');
			$('#form_btn_tips').html('<font color=green>保存成功！</font>');
			setTimeout(function() { window.location.href = '?man,' + qa[1]; }, 500);
		});
	}
}

function edit_form_preview(e) {
	e.preventDefault();

	if (!edit_has_field_empty()) {
		$('#form_btn_tips').html('预览生成中，请稍后 ...');
		$(e.target).addClass('disabled');

		var s = get_all_field_in();
		$.post('getinfo.py?preview', s, function(d) {
			$('#form_btn_tips').html('');
			$(e.target).removeClass('disabled');
			console.log(d);
			window.open(d);
		});
	}
}

function edit_add_btn_click(e) {
	e.preventDefault();
	var tid = $(e.target).attr('tid');
	console.log(tid);
	var v = (tid == 'substr_addr') ? '' : ['',''];
	$(template(tid, {del:1, v:v})).insertBefore($(e.target).parent());
}

function edit_del_btn_click(e) {
	e.preventDefault();
	var div = $(e.target).closest('div');
	div.fadeOut(150, function() { $(this).remove(); });
}

function radio_show_index(id, n) {
	$('#tabs_' + id).html(template(id + n, {}));
}

function edit_radio_tab_click(e) {
	var n = $(e.target).val();
	radio_show_index($(e.target).attr('name'), n);
}

function get_h2(id) {
	var left = template('index_' + id, {});
	var h2 = $($(left)[0]).html();
	return h2;
}

function show_edit() {
	var a = (qa[0] == 'add') ? 'new' : 'load,'+qa[2];	
	$.post('getinfo.py?' + a, {}, _show_edit);
}

function multi_in(t, a) {
	var r = '';
	for (i in a) {
		r += template(t, {del:i, v:a[i]});
	}
	return r;
}

template.helper('getval', function (c) {
	return gr[c];
});
template.helper('atoi', function (c) {
	return parseInt(c);
});

function _show_edit(_d) {

//	console.log(_d);
	var r = jQuery.parseJSON(_d);
	gr = r;

	/*
	r.host = 'host50';
	r.alias = '测试';
	r.in_2 = [['www.x', 'aaa'], ['apple', 'banana']];
	r.in_n = ['aaa', 'ccc', 'dddd'];
	r.subip = '192.168.1.1';
	r.subsrc = '山东联通';
	r.baidu_tab = 2;
	r.ads_name = 'ads_name';
	r.ads_link = 'ads_link';
	r.ads_html = '<h1>ads_desc</h1>';
	r.keywords = 'k1 k2 k3';
	*/

	var hosts_html = '<option>请选择</option>';
	for (i in r.hosts) {
		var h = r.hosts[i];
		var sd = (r.host == h) ? 'selected' : '';
		hosts_html += '<option value=' + h + ' ' + sd +' >' + h + '</option>';
	}
	var left = template('index_' + qa[1], {});
	var h2 = get_h2(qa[1]);
	var html = template('edit_form_header', {hosts:hosts_html, r:r});

	if (qa[1] == 'substr') {
		if (qa[0] == 'add') {
			r.in_n = [''];
			r.in_2 = [['', '']];
		}
		html += template('edit_substr', {
			addr:multi_in('substr_addr', r.in_n), 
			sub:multi_in('substr_sub', r.in_2),
			r:r,
		});
	}
	if (qa[1] == 'subip') {
		if (qa[0] == 'add') {
			r.in_n = [''];
		}
		html += template('edit_subip', {
			addr:multi_in('substr_addr', r.in_n), 
			r:r
		});
	}
	if (qa[1] == 'baidu') {
		html += template('edit_baidu', {});
	}
	if (qa[1] == 'taobao') {
		html += template('edit_taobao', {});
	}
	if (qa[1] == 'sohu') {
		html += template('edit_sohu', {});
	}
	if (qa[1] == 'zol') {
		html += template('edit_zol', {});
	}
	if (qa[1] == 'job51') {
		html += template('edit_job51', {});
	}

	var form = template('edit_form', {html:html, h2:'添加策略：' + h2});
	$('#main_div').html(template('edit_html', {left:left, form:form}));
}

function upload_onchange(e) {
	console.log($(e.target));
	console.log($(e.target).val());
	console.log(e.target.files[0]);
	errmsg = $(e.target).parent().find('.form-errmsg');
	errmsg.html('');
	$('#upload-msg').html('');
	$('#upload-img-bar').hide();
	file = e.target.files[0];
	console.log(file.size);
	if (!file.type.match(/^image/) || file.size > 10*1024*1024) {
		errmsg.html('警告：必须上传图像文件而且大小不能大于10MB！');
		return ;
	}

	$(e.target).prop('disabled', true);
	console.log($('#upload-img-bar'));
	$('#upload-img-bar div').css({width:'0%'});
	$('#upload-img-bar').show();

	var xhr = new XMLHttpRequest();
	xhr.upload.onprogress = function (e) {
		var per = (e.loaded / e.total) * 100 + '%';
		$('#upload-img-bar div').css('width', per);
		console.log(e.loaded, e.total, per);
	};
	xhr.open('POST', 'getinfo.py?upload,' + file.name, true);
	xhr.setRequestHeader('Content-Type', "application/octet-stream");
	xhr.onreadystatechange = function() {
		if (xhr.readyState == 4) {
			$('#upload-msg').html('上传完毕');
			$('#upload-file').prop('disabled', false);
			var path = xhr.responseText + file.name;
			$('#upload-img img').attr('src', path);
			$('#upload-img').show();
			$('[field_in=upload_img_path]').val(path);
		}
	};
	xhr.send(file);
}

function man_tr_del_click(e) {
	var id = $(e.target).closest('tr').attr('id');
	if (confirm('确认删除？')) {
		$(e.target).addClass('disabled');
		$.post('getinfo.py?del,' + id, {}, function() {
			window.location.reload();
		});
	}
}

function man_tr_edit_click(e) {
	var id = $(e.target).closest('tr').attr('id');
	var cat = $(e.target).closest('tr').attr('cat');
	window.location.href = '?edit,' + cat + ',' + id;
}

function show_man() {
	$.post('getinfo.py?list', {}, _show_man);
}

function _show_man(_d) {
	var r = jQuery.parseJSON(_d);
	var cat = {};
	var li = '';
	var tr = '';

	for (i in r) {
		var c = r[i].cat;
		if (!(c in cat)) {
			cat[c] = [];
		}
		cat[c].push(r[i]);
	}

	var sel = '';
	var arr = [];
	for (c in cat) {
		arr.push(c);
		if (qa[1] == c) {
			sel = c;
		}
	}
	var first = arr[0];
	if (sel == '') {
		sel = first;
	}
	
	for (c in cat) {
		var h2 = get_h2(c);
		if (c == sel) {
			cls = 'class=active ';
		} else {
			cls = '';
		}
		li += '<li ' + cls + ' ><a href=?man,' + c + '>' + h2 + '</a></li>';
	}
	for (i in cat[sel]) {
		tr += template('man_tr', {r:cat[sel][i]});
	}

	$('#main_div').html(template('man_html', {li:li, tr:tr}));
}

function nav_active(n) {
	$($('#topnav > li')[n]).addClass('active');
}

function show_index_videos() {
	$.post('cgi.py?ls', {}, function(d) {
		console.log(d);
		var r = jQuery.parseJSON(d);
		var html = '';
		for (var k in r) {
			console.log(k);
			html += template('thumb_span', {r:r[k]});
		}
		$('#main_div').html(template('index_videos', {html:html}));
	});
}

qs = window.location.search.substr(1);
qa = qs.split(',');

$(document).ready(function() {
	show_index_videos();
	return ;
	if (qa[0] == 'add' || qa[0] == 'edit') {
		nav_active(0);
		show_edit();
	} else if (qa[0] == 'man') {
		nav_active(1);
		show_man();
	} else {
		nav_active(0);
		show_index();
	}
});

