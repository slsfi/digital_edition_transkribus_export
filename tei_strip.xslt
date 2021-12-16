<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
 
 <!-- Output xml for the sax parser -->
 <xsl:output method="xml"/>
 
 <!-- Include all elements that spaces should be stripped from in the list below-->
 <xsl:strip-space elements="tei:body tei:text tei:div tei:lg tei:p tei:l tei:dateline"/>

<!-- Root element -->
<xsl:template match="/">
  <TEI>
    <xsl:apply-templates select="tei:TEI/tei:text/tei:body"/>
  </TEI>
</xsl:template>

<!-- Body element -->
<xsl:template match="tei:body">
  <xsl:apply-templates />
</xsl:template>

<!-- Block elements that should result in line breaks -->
<xsl:template match="tei:head | tei:p | tei:lg | tei:l | tei:opener | tei:closer">
  <xsl:apply-templates />
  <br/>
  <xsl:if test="name()='head'">
    <br/>
  </xsl:if>
</xsl:template>

<!-- Page breaks, inlcude only breaks with type=orig -->
<xsl:template match="tei:pb">
  <xsl:if test="@type='orig'">
    <pb>
      <xsl:attribute name="n">
        <xsl:value-of select="@n"/>
      </xsl:attribute>
    </pb>
  </xsl:if>
</xsl:template>

<!-- Include all elements that should be copied in the list below -->
<!--<xsl:template match="tei:add | tei:del">
  <xsl:copy-of select="." />
</xsl:template>-->

<!-- Include all elements that should be removed in the list below -->
<!-- Is the original version preferred, in that case tei:reg and te:corr are removed -->
<xsl:template match="tei:note | tei:reg | tei:corr | tei:expan" />

<!-- Below are templates to copy a without adding xmlns to all copied elements -->
<xsl:template match="*" mode="copy">
  <xsl:element name="{name()}" namespace="{namespace-uri()}">
    <xsl:apply-templates select="@*|node()" mode="copy" />
  </xsl:element>
</xsl:template>

<xsl:template match="@*|text()|comment()" mode="copy">
  <xsl:copy/>
</xsl:template>

</xsl:stylesheet>