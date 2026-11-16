# Imagem do Jenkins do projeto (publicada no Docker Hub)
FROM jenkins/jenkins:lts-jdk21

USER root
# Tudo que o pipeline precisa fica instalado AQUI, nunca na máquina do aluno:
# Python (testes e script de e-mail), venv/pip, zip (empacotamento) e git (checkout).
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip python3-venv zip git \
 && rm -rf /var/lib/apt/lists/*

USER jenkins

# Plugins instalados na construção da imagem
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Jenkins Configuration as Code: usuário admin e job do pipeline definidos em arquivo
COPY --chown=jenkins:jenkins casc.yaml /usr/share/jenkins/casc_configs/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/casc_configs/casc.yaml
# Sem o assistente de instalação (a configuração já vem do casc.yaml)
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
