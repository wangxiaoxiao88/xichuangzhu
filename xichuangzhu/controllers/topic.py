#-*- coding: UTF-8 -*-

import cgi
import markdown2
from flask import render_template, request, redirect, url_for, json, session
from xichuangzhu import app
from xichuangzhu.models.topic_model import Topic
from xichuangzhu.models.node_model import Node
from xichuangzhu.models.comment_model import Comment
from xichuangzhu.models.user_model import User
from xichuangzhu.models.inform_model import Inform
from xichuangzhu.form import TopicForm, CommentForm
from xichuangzhu.utils import time_diff, require_login, get_comment_replyee_id, rebuild_comment, build_topic_inform_title

# page topics
#--------------------------------------------------
@app.route('/topics')
def topics():
	topics = Topic.get_topics(15)
	for t in topics:
		t['Time'] = time_diff(t['Time'])

	nodes = Node.get_nodes(16)

	hot_topics = Topic.get_hot_topics(10)
	
	node_types = Node.get_types()
	for nt in node_types:
		nt['nodes'] = Node.get_nodes_by_type(nt['TypeID'])

	return render_template('topic/topics.html', topics=topics, nodes=nodes, hot_topics=hot_topics, node_types=node_types)

# page single topic
#--------------------------------------------------
@app.route('/topic/<int:topic_id>')
def single_topic(topic_id):
	form = CommentForm()
	topic = Topic.get_topic(topic_id)
	topic['Time'] = time_diff(topic['Time'])
	topic['Content'] = markdown2.markdown(topic['Content'])
	comments = Comment.get_comments_by_topic(topic['TopicID'])
	for c in comments:
		c['Time'] = time_diff(c['Time'])
	Topic.add_click_num(topic_id)
	nodes = Node.get_nodes(16)
	
	return render_template('topic/single_topic.html', topic=topic, comments=comments, nodes=nodes, form=form)

# proc - add comment
@app.route('/topic/<int:topic_id>', methods=['POST'])
@require_login
def add_comment_to_topic(topic_id):
	form = CommentForm(request.form)	
	if form.validate():
		comment = cgi.escape(form.comment.data)

		# add comment
		replyer_id = session['user_id']
		replyee_id = get_comment_replyee_id(comment)	# check if @people exist
		if replyee_id != -1:
			comment = rebuild_comment(comment, replyee_id)
		new_comment_id = Comment.add_comment_to_topic(topic_id, replyer_id, comment)

		# plus comment num by 1
		Topic.add_comment_num(topic_id)

		# add inform
		topic_user_id = Topic.get_topic(topic_id)['UserID']
		inform_title = build_topic_inform_title(replyer_id, topic_id)
		# if the topic not add by me
		if replyer_id != topic_user_id:
			Inform.add(replyer_id, topic_user_id, inform_title, comment)
		# if replyee exist,
		# and the topic not add by me,
		# and not topic_user_id, because if so, the inform has already been sended above
		if replyee_id != -1 and  replyee_id != replyer_id and replyee_id != topic_user_id:
			Inform.add(replyer_id, replyee_id, inform_title, comment)
		return redirect(url_for('single_topic', topic_id=topic_id) + "#" + str(new_comment_id))
	else:
		return redirect(url_for('single_topic', topic_id=topic_id))

# page add topic
#--------------------------------------------------

# view (login)
@app.route('/topic/add', methods=['POST', 'GET'])
@require_login
def add_topic():
	node_types = Node.get_types()
	for nt in node_types:
		nt['nodes'] = Node.get_nodes_by_type(nt['TypeID'])

	if request.method == 'GET':
		# choose a node to be default, here is node_id = 10001
		node_id = int(request.args['node_id']) if "node_id" in request.args else 10001
		form = TopicForm(node_id=node_id)
		node = Node.get_node_by_id(node_id)
		return render_template('topic/add_topic.html', node=node, node_types=node_types, form=form)
	else:
		form = TopicForm(request.form)
		if form.validate():
			# node_id = int(form.node_id.data)
			node_id = 10001
			title = cgi.escape(form.title.data)
			content = cgi.escape(form.content.data)
			user_id = session['user_id']
			new_topic_id = Topic.add(node_id, title, content, user_id)
			return redirect(url_for('single_topic', topic_id=new_topic_id))
		else:
			# choose a node to be default, here is node_id = 10001
			# node_id = int(form.node_id.data)
			node_id = 10001
			node = Node.get_node_by_id(node_id)
			return render_template('topic/add_topic.html', node=node, node_types=node_types, form=form)


# page edit topic
#--------------------------------------------------
@app.route('/topic/edit/<int:topic_id>', methods=['POST', 'GET'])
@require_login
def edit_topic(topic_id):
	# auth check
	topic = Topic.get_topic(topic_id)
	if topic['UserID'] != session['user_id']:
		abort(404)

	node_types = Node.get_types()
	for nt in node_types:
		nt['nodes'] = Node.get_nodes_by_type(nt['TypeID'])

	if request.method == 'GET':
		form = TopicForm(node_id=topic['NodeID'], title=topic['Title'], content=topic['Content'])
		return render_template('topic/edit_topic.html', topic=topic, node_types=node_types, form=form)
	else:
		form = TopicForm(request.form)
		if form.validate():
			# node_id = int(form.node_id.data)
			node_id = 10001
			title = cgi.escape(form.title.data)
			content = cgi.escape(form.content.data)
			new_topic_id = Topic.edit(topic_id, node_id, title, content)
			return redirect(url_for('single_topic', topic_id=topic_id))
		else:
			return render_template('topic/edit_topic.html', topic=topic, node_types=node_types, form=form)


# page single node
#--------------------------------------------------
@app.route('/node/<node_abbr>')
def single_node(node_abbr):
	node = Node.get_node_by_abbr(node_abbr)
	nodes = Node.get_nodes(16)
	topics = Topic.get_topics_by_node(node_abbr)
	for t in topics:
		t['Time'] = time_diff(t['Time'])
	return render_template('topic/single_node.html', node=node, nodes=nodes, topics=topics)