<!DOCTYPE html>
<html lang="en">
	<head>
		<link rel="stylesheet" href="${base}css/style.css">
    <%block name="css_block"></%block>
		<script type="text/javascript" >var _base = "${base}";</script>
		<script src="${base}js/script.js"></script>
    <script>$(document).ready(function(){$(".mainbody").focus();});</script>
    <%block name="js_block"></%block>
    <title><%block name="title_block"></%block></title>
	</head>
  <body>
    ${self.body()}
  </body>
</html>