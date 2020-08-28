{ pkgs ? import <nixpkgs> {}}: 
with pkgs;
let
  my-python-packages = python-packages: with python-packages; [
    jinja2
    pip
  ]; 
  python-with-my-packages = python3.withPackages my-python-packages;
in mkShell {
  buildInputs = [
    python-with-my-packages
  ];
  shellHook = ''
            alias pip="PIP_PREFIX='$(pwd)/_build/pip_packages' \pip"
            export PYTHONPATH="$(pwd)/_build/pip_packages/lib/python3.8/site-packages:$PYTHONPATH"
            unset SOURCE_DATE_EPOCH
  '';
}
