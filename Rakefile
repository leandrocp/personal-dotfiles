require 'rake'
require 'erb'

task :default => 'install:all'

namespace :install do

  desc "install and configure everything"
  task :all => [:dotfiles, :rvm, :gedit] do
    puts "Happy coding!"
  end

  desc "install the dot files into user's home directory"
  task :dotfiles do
    replace_all = false
    Dir['*'].each do |file|
      next if %w[Rakefile README.rdoc LICENSE gedit bin].include? file

      if File.exist?(File.join(ENV['HOME'], ".#{file.sub('.erb', '')}"))
        if File.identical? file, File.join(ENV['HOME'], ".#{file.sub('.erb', '')}")
          puts "identical ~/.#{file.sub('.erb', '')}"
        elsif replace_all
          replace_file(file)
        else
          print "overwrite ~/.#{file.sub('.erb', '')}? [ynaq] "
          case $stdin.gets.chomp
          when 'a'
            replace_all = true
            replace_file(file)
          when 'y'
            replace_file(file)
          when 'q'
            exit
          else
            puts "skipping ~/.#{file.sub('.erb', '')}"
          end
        end
      else
        link_file(file)
      end
    end
  end

  desc "install and configure rvm, the Ruby Version Manager"
  task :rvm do
    puts "Installing rvm and dependencies"
    system %Q{sudo apt-get install curl git-core patch}
    system %Q{su -c "bash < <( curl -L http://bit.ly/rvm-install-system-wide )"}
    puts "Adding user to the group 'rvm'"
    system %Q{sudo usermod -a -G rvm $USER}
    puts "Reloading rvm"
    system %Q{rvm reload}
    puts `type rvm | head -n1`
    puts 'Done installing rvm'
  end

  desc "install and configure gedit"
  task :gedit do
    if File.directory?(File.join(ENV['HOME'], "/.gnome2"))
      if File.identical? File.join(ENV['PWD'], "/gedit"), File.join(ENV['HOME'], "/.gnome2/gedit")
        puts "identical ~/.gnome2/gedit"
      else
        print "overwrite ~/.gnome2/gedit? [yn] "
        case $stdin.gets.chomp
        when 'y'
          system %Q{rm -rf "$HOME/.gnome2/gedit"}
          puts "linking ~/.gnome2/gedit"
          system %Q{ln -s "$PWD/gedit" "$HOME/.gnome2/"}
          system %Q{sh "$HOME/.gnome2/gedit/install.sh"}
        else
          puts "skipping ~/.gnome2/gedit"
        end
      end
    else
      puts "gnome2 is not installed"
      puts "skipping ~/.gnome2/gedit"
    end
  end

  desc "install bin"
  task :bin do
    Dir['bin/*'].each do |file|
      link_bin(file)
    end
  end
end

def replace_file(file)
  system %Q{rm -rf "$HOME/.#{file.sub('.erb', '')}"}
  link_file(file)
end

def link_file(file)
  if file =~ /.erb$/
    puts "generating ~/.#{file.sub('.erb', '')}"
    File.open(File.join(ENV['HOME'], ".#{file.sub('.erb', '')}"), 'w') do |new_file|
      new_file.write ERB.new(File.read(file)).result(binding)
    end
  else
    puts "linking ~/.#{file}"
    system %Q{ln -s "$PWD/#{file}" "$HOME/.#{file}"}
  end
end

def link_bin(file)
  bin = File.join(ENV['PWD'], '/', file)
  system %Q{sudo rm /usr/#{file}}
  system %Q{sudo ln -s #{bin} /usr/#{file}}
end
